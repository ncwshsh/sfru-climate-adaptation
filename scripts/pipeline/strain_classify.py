# -*- coding: utf-8 -*-
"""strain_classify.py —— 用 Tpi/Flightin 标记区给全队列判定玉米型(C)/水稻型(R)

★ 方法论（这步最容易出错，所以按"先验证、后应用"来做）：
  1. **训练**：美国 143 个样本有 NCBI 官方株系标注（C 80 / R 62 / H 1，H 型剔除），
     用它们学一个判别分数：对每个标记位点算 d = mean(剂量_C) − mean(剂量_R)，
     样本得分 S = Σ d_i × dose_i（未中心化的常数项不影响分类）
  2. **留一交叉验证（LOO）**：留一个样本，只用其余样本算 d_i，再预测被留出的那个
     —— 这是唯一能老实估计准确率的办法；不验证就直接套用，等于把误差带进所有下游结论
  3. **应用**：只有 LOO 准确率达标（≥90%）才对非美国样本分型
  4. 输出每个样本的预测株系 + 得分 + 置信度（得分离两类中心的相对距离）
"""
import os
import numpy as np
import pandas as pd

ROOT = "/mnt/c/SF_data"
GENO = "/home/hugo/data/angsd/strain_region_geno.tsv"
GEA = os.path.join(ROOT, "tools", "report", "gea_input.tsv")
HOST = os.path.join(ROOT, "tools", "report", "host_sra.tsv")
BAMLIST = os.path.join(ROOT, "tools", "bamlist_keep214.txt")   # ⚠️ 必须与 beagle 的列数一致（beagle 基于 214 样本生成）
OUT = os.path.join(ROOT, "tools", "report", "strain_predicted.tsv")
import re
PAT = re.compile(r"identified as ([CRH])[- ]*strain", re.I)


def read_meta():
    runs = [os.path.basename(l.strip()).split(".")[0] for l in open(BAMLIST) if l.strip()]
    gea = {r["run"]: r for r in pd.read_csv(GEA, sep="\t").to_dict("records")}
    lab = {}
    for r in pd.read_csv(HOST, sep="\t").to_dict("records"):
        blob = " ".join(str(v) for k, v in r.items() if k != "run")
        m = PAT.search(blob)
        if m:
            lab[r["run"]] = m.group(1).upper()
    return runs, gea, lab


def main():
    runs, gea, lab = read_meta()
    n = len(runs)
    d = pd.read_csv(GENO, sep="\t")
    mk = d["marker"].values
    reg = d["region"].values
    pos = d["pos"].values
    D = d.iloc[:, 3:].values.astype(np.float64)      # 位点 × 220
    print("标记位点 %d 个（%s），样本 %d 个" % (D.shape[0], dict(zip(*np.unique(reg, return_counts=True))), n))

    # 训练集：美国且标注 C/R（剔除 H）
    tr = np.array([i for i, r in enumerate(runs) if lab.get(r) in ("C", "R")])
    y = np.array([1.0 if lab[runs[i]] == "C" else 0.0 for i in tr])
    print("训练集：%d 个（C=%d, R=%d）" % (len(tr), int(y.sum()), int((1 - y).sum())))
    Xtr = D[:, tr]                                   # 位点 × 训练样本

    def score(train_idx, target_cols):
        """用 train_idx 学 d，再给 target_cols 打分"""
        Xt = D[:, train_idx]
        yt = np.array([1.0 if lab[runs[i]] == "C" else 0.0 for i in train_idx])
        dvec = Xt[:, yt == 1].mean(1) - Xt[:, yt == 0].mean(1)
        w = np.abs(dvec)
        keep = w > 1e-6                              # 丢掉无信息位点
        return (D[keep][:, target_cols] * dvec[keep, None]).sum(0), int(keep.sum())

    # ---- 1. 全训练集打分（用于定阈值与置信度）----
    s_tr, nk = score(tr, tr)
    c_mid, r_mid = s_tr[y == 1].mean(), s_tr[y == 0].mean()
    s_all, _ = score(tr, np.arange(n))
    print("训练集打分：C 中心 %.1f，R 中心 %.1f（用了 %d 个有信息的位点）" % (c_mid, r_mid, nk))

    # ---- 2. LOO 交叉验证 ----
    loo_pred = np.zeros(len(tr))
    for k, i in enumerate(tr):
        other = np.array([j for j in tr if j != i])
        s1, _ = score(other, np.array([i]))
        st, _ = score(other, other)
        yo = np.array([1.0 if lab[runs[j]] == "C" else 0.0 for j in other])
        mid = (st[yo == 1].mean() + st[yo == 0].mean()) / 2.0
        loo_pred[k] = 1.0 if s1[0] > mid else 0.0
    acc = float((loo_pred == y).mean())
    tp = int(((loo_pred == 1) & (y == 1)).sum()); fn = int(((loo_pred == 0) & (y == 1)).sum())
    tn = int(((loo_pred == 0) & (y == 0)).sum()); fp = int(((loo_pred == 1) & (y == 0)).sum())
    print()
    print("=== 留一交叉验证结果 ===")
    print("  准确率 %.3f   混淆矩阵：C 正确 %d / 误判 %d ；R 正确 %d / 误判 %d" % (acc, tp, fn, tn, fp))
    if acc < 0.9:
        print("  ⚠ 准确率不足 0.90，用这个标记集给其他模块分型有风险，结果只能作探索性参考")

    # ---- 3. 全样本判定 ----
    mid = (c_mid + r_mid) / 2.0
    pred = np.where(s_all > mid, "C", "R")
    span = abs(c_mid - r_mid)
    conf = np.abs(s_all - mid) / (span / 2.0)         # 1.0 = 正好落在某一类中心
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("run\tmodule\tstrain_known\tstrain_pred\tscore\tconfidence\n")
        for i, r in enumerate(runs):
            fh.write("%s\t%s\t%s\t%s\t%.1f\t%.2f\n"
                     % (r, gea.get(r, {}).get("module", ""), lab.get(r, ""),
                        pred[i], s_all[i], min(conf[i], 9.99)))
    print()
    print("已写出: %s" % OUT)

    # ---- 4. 各模块株系构成 ----
    print()
    print("=== 各模块的株系构成（分子判定）===")
    mod = np.array([gea.get(r, {}).get("module", "") for r in runs])
    print("%-4s %6s %6s %6s %8s" % ("模块", "样本", "C型", "R型", "平均置信"))
    for m in ["US", "BR", "AF", "AM", "CN", "FL"]:
        sel = mod == m
        if not sel.any():
            continue
        pc = int((pred[sel] == "C").sum())
        pr = int((pred[sel] == "R").sum())
        print("%-4s %6d %6d %6d %8.2f" % (m, sel.sum(), pc, pr, conf[sel].mean()))

    # ---- 5. 美国样本：已知 vs 预测 一致性 ----
    us_known = np.array([lab.get(r, "") for r in runs])
    sel = (mod == "US") & (us_known != "") & (us_known != "H")
    if sel.any():
        agree = float((pred[sel] == us_known[sel]).mean())
        print()
        print("=== 美国样本（有官方标注）：分子判定与标注一致率 %.1f%%（n=%d）===" % (100 * agree, sel.sum()))
        bad = [runs[i] for i in np.where(sel)[0] if pred[i] != us_known[i]]
        if bad:
            print("  不一致样本：%s" % ", ".join(bad[:10]))


if __name__ == "__main__":
    main()
