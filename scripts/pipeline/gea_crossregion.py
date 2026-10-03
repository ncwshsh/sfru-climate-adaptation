# -*- coding: utf-8 -*-
"""gea_crossregion.py —— 玉米型内部的跨国气候适应对比

背景：株系判定发现三个入侵地（巴西/非洲/中国）几乎清一色玉米型，
      所以"株系维度"的跨国对比没有对照组，只能在**玉米型内部**比地区。

分析设计（三层）：
  ① 分模块 partial RDA：US-C(80) / BR(24) / AF(16) / AM-C(14) / CN(10) 各自跑，
     看每个地区有没有自己的气候关联信号、强度如何
  ② 候选位点的跨地区一致性：取美国（样本最多、功效最好）的 top 位点，
     看它们在其他地区是否也比背景位点更强——**这是"气候适应是否跨地区共有"的关键检验**
  ③ 各模块候选位点的重叠度（Jaccard）

⚠️ 样本量差异巨大，模型复杂度必须自适应，否则小模块过拟合：
      n < 15 → 气候 1 轴 + 结构 1 PC
      n < 30 → 气候 2 轴 + 结构 2 PC
      n ≥ 30 → 气候 3 轴 + 结构 3 PC
   小模块（CN 10、AF 16）的结果只能定性看方向，不能当独立结论。
"""
import os
import sys
import numpy as np
import pandas as pd

ROOT = "/mnt/c/SF_data"
BEAGLE = "/home/hugo/data/angsd/beagle_1M.beagle.gz"
GEA = os.path.join(ROOT, "tools", "report", "gea_input.tsv")
CLIMT = os.path.join(ROOT, "tools", "report", "climate_s2.tsv")
PCA = "/home/hugo/data/angsd/pca_scores.tsv"
BAMLIST = os.path.join(ROOT, "tools", "bamlist_keep214.txt")
# ---- 敏感性分析支持（2026-09-24 加）----
#   EXCL_FILE=<路径>  读入要剔除的 run 列表（每行一个，# 开头为注释）
#   SUFFIX=<后缀>     所有输出加后缀，避免覆盖原结果
SUFFIX = os.environ.get("SUFFIX", "")
EXCL_FILE = os.environ.get("EXCL_FILE", "")
OUT = os.path.join(ROOT, "tools", "report", "gea_crossregion%s.tsv" % SUFFIX)
OUTP = os.path.join(ROOT, "tools", "report", "gea_crossregion%s.png" % SUFFIX)
NPERM = 499
SEED = 42


def load():
    runs = [os.path.basename(l.strip()).split(".")[0] for l in open(BAMLIST) if l.strip()]
    meta = pd.read_csv(GEA, sep="\t").set_index("run").loc[runs].reset_index()
    climt = pd.read_csv(CLIMT, sep="\t").set_index("run")
    bio = ["bio%d" % i for i in range(1, 20)]
    clim = climt.loc[runs, bio].astype(float).values
    pcs = pd.read_csv(PCA, sep="\t").set_index("run").loc[runs, ["PC1", "PC2", "PC3", "PC4"]].values
    return runs, meta, clim, pcs


def region_rda(Y, clim, pcs, rng):
    """对一个模块做 partial RDA，返回 (R2, p, z1)"""
    n = Y.shape[1]
    if n < 8:
        return None
    if n < 15:
        kc, kp = 1, 1
    elif n < 30:
        kc, kp = 2, 2
    else:
        kc, kp = 3, 3

    cz = (clim - clim.mean(0)) / (clim.std(0) + 1e-9)
    C = np.corrcoef(cz.T)
    keepc = []
    for i in range(C.shape[0]):
        if all(abs(C[i, j]) < 0.9 for j in keepc):
            keepc.append(i)
    cz = cz[:, keepc]
    Uc, Sc, _ = np.linalg.svd(cz - cz.mean(0), full_matrices=False)
    X = Uc[:, :kc] * Sc[:kc]
    X = (X - X.mean(0)) / (X.std(0) + 1e-9)

    Z = np.column_stack([np.ones(n), pcs[:, :kp]])
    Z = Z[:, Z.std(0) > 1e-9]

    def resid(A):
        A = A - A.mean(0)
        Zc = Z - Z.mean(0)
        beta, *_ = np.linalg.lstsq(Zc, A, rcond=None)
        return A - Zc @ beta

    Yr = resid(Y.T).T
    Xr = resid(X)
    Xr = (Xr - Xr.mean(0)) / (Xr.std(0) + 1e-9)

    G = Yr.T @ Yr
    XtX_inv = np.linalg.pinv(Xr.T @ Xr)
    P = Xr @ XtX_inv @ Xr.T
    inertia = float(np.trace(P @ G))
    tot = float(np.trace(G))
    r2 = inertia / tot

    cnt = 0
    for _ in range(NPERM):
        idx = rng.permutation(n)
        if float(np.trace(Xr[idx] @ XtX_inv @ Xr[idx].T @ G)) >= inertia:
            cnt += 1
    pval = (cnt + 1) / (NPERM + 1)

    Gy = P @ G @ P
    w, v = np.linalg.eigh(Gy)
    o = np.argsort(w)[::-1]
    w = np.maximum(w[o], 0)
    U = v[:, o][:, :1]
    S = np.sqrt(w[:1])
    A = P @ U
    # 载荷 = Yr @ A / S  （Yr: 位点×n, A: n×1）
    # ⚠️ 写成 Yr.T @ A 会维度不匹配——A = P@U 已经作用在样本维度上
    load = (Yr @ A / S).ravel()
    z1 = (load - load.mean()) / (load.std() + 1e-12)
    return r2, pval, z1, (kc, kp)


def main():
    rng = np.random.default_rng(SEED)
    runs, meta, clim, pcs = load()

    # ---- 可选：剔除指定样本（敏感性分析）----
    keep = None
    if EXCL_FILE and os.path.exists(EXCL_FILE):
        EXCL = set(l.strip() for l in open(EXCL_FILE, encoding="utf-8")
                   if l.strip() and not l.startswith("#"))
        miss = EXCL - set(runs)
        keep = np.array([r not in EXCL for r in runs])
        print("★★ 敏感性分析：剔除 %d 个样本，保留 %d / %d"
              % (int((~keep).sum()), int(keep.sum()), len(runs)))
        for r in sorted(EXCL & set(runs)):
            print("     剔除 %s" % r)
        if miss:
            print("     ⚠️ 不在 bamlist 中、已忽略: %s" % ", ".join(sorted(miss)))
        runs = [r for r, k in zip(runs, keep) if k]
        meta = meta[keep].reset_index(drop=True)
        clim = clim[keep]
        pcs = pcs[keep]

    strain = meta["strain"].values
    mod = meta["module"].values

    # 分析单位：玉米型样本按地区分组
    groups = {
        "US-C": mod == "US",
        "BR-C": mod == "BR",
        "AF-C": mod == "AF",
        "AM-C": mod == "AM",
        "CN-C": mod == "CN",
    }
    print("读基因型…")
    df = pd.read_csv(BEAGLE, sep=r"\s+", dtype={0: str})
    gl = df.iloc[:, 3:].values
    Yall = (gl[:, 1::3].astype(np.float64) + 2.0 * gl[:, 2::3].astype(np.float64))
    if keep is not None:
        assert Yall.shape[1] == len(keep), \
            "beagle 列数 %d 与样本数 %d 不符" % (Yall.shape[1], len(keep))
        Yall = Yall[:, keep]
    markers = df.iloc[:, 0].values
    print("  位点 %d" % Yall.shape[0])

    res = {}
    print()
    print("%-6s %5s %10s %8s %10s" % ("组", "样本", "R²", "置换p", "模型(k气候,k结构)"))
    for g, sel in groups.items():
        sel = sel & (strain == "C")
        if sel.sum() < 8:
            print("%-6s %5d  样本不足，跳过" % (g, sel.sum()))
            continue
        r = region_rda(Yall[:, sel], clim[sel], pcs[sel], rng)
        if r is None:
            continue
        r2, pv, z1, kk = r
        res[g] = dict(sel=sel, z1=z1, r2=r2, p=pv, kk=kk)
        print("%-6s %5d %10.4f %8.4f %10s" % (g, sel.sum(), r2, pv, kk))
        # 存下该地区全部位点的 z（供后续"同口径候选基因集比较"用）
        with open(os.path.join(ROOT, "tools", "report",
                               "crossregion_z_%s%s.tsv" % (g, SUFFIX)), "w",
                  encoding="utf-8") as fh:
            fh.write("marker\tz\n")
            fh.writelines("%s\t%.4f\n" % (markers[i], z1[i]) for i in range(len(z1)))

    # ---- 跨地区一致性：美国的 top 位点在别处是否也强 ----
    if "US-C" in res:
        print()
        print("=== 跨地区一致性检验 ===")
        print("  取美国的 top 1%% 位点，看它们在每个地区里的 |z| 是否高于该地区背景")
        z_us = np.abs(res["US-C"]["z1"])
        thr = np.quantile(z_us, 0.99)
        topmask = z_us >= thr
        print("  美国 top 1%% 阈值 |z| >= %.3f（位点 %d 个）" % (thr, topmask.sum()))
        rows = []
        for g in res:
            zg = np.abs(res[g]["z1"])
            bg = zg.mean()
            obs = zg[topmask].mean()
            # 置换：随机取同样多的位点
            cnt = 0
            for _ in range(2000):
                r = rng.choice(len(zg), size=int(topmask.sum()), replace=False)
                if zg[r].mean() >= obs:
                    cnt += 1
            pv = (cnt + 1) / 2001
            rows.append((g, obs, bg, obs - bg, pv))
            print("    %-6s 美国top位点 |z|均值 %.3f  该地区背景 %.3f  差 %+.3f  置换p %.4f"
                  % (g, obs, bg, obs - bg, pv))
        with open(OUT, "w", encoding="utf-8") as fh:
            fh.write("group\tn\tR2\tp_rda\ttop_mean_z\tbg_mean_z\tdiff\tp_perm\n")
            for (g, obs, bg, diff, pv) in rows:
                fh.write("%s\t%d\t%.4f\t%.4f\t%.3f\t%.3f\t%+.3f\t%.4f\n"
                         % (g, res[g]["sel"].sum(), res[g]["r2"], res[g]["p"], obs, bg, diff, pv))
        print()
        print("已写出: %s" % OUT)

    # ---- 图 ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    gs = list(res.keys())
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))
    r2s = [res[g]["r2"] for g in gs]
    ax[0].bar(gs, r2s, color=["#c0392b" if g == "US-C" else "#7f8c8d" for g in gs])
    for i, v in enumerate(r2s):
        ax[0].text(i, v, "%.3f" % v, ha="center", va="bottom", fontsize=9)
    ax[0].set_ylabel("R² (climate explained)")
    ax[0].set_title("Climate signal by region\n(only corn-strain samples)", fontsize=10)

    # |z| 分布对比
    for g in gs:
        z = np.abs(res[g]["z1"])
        ax[1].hist(z, bins=80, histtype="step", lw=1.2, label="%s (n=%d)" % (g, res[g]["sel"].sum()))
    ax[1].set_xlim(0, 6)
    ax[1].set_xlabel("|z| of RDA1 loading"); ax[1].set_ylabel("SNPs")
    ax[1].legend(fontsize=8)
    ax[1].set_title("|z| distribution by region", fontsize=10)

    if "US-C" in res:
        z_us = np.abs(res["US-C"]["z1"])
        thr = np.quantile(z_us, 0.99)
        tm = z_us >= thr
        means = [np.abs(res[g]["z1"])[tm].mean() for g in gs]
        ax[2].bar(gs, means, color="#2980b9")
        for i, v in enumerate(means):
            ax[2].text(i, v, "%.2f" % v, ha="center", va="bottom", fontsize=9)
        ax[2].set_ylabel("mean |z| of US top-1% SNPs")
        ax[2].set_title("Are US climate candidates also\nstrong in other regions?", fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTP, dpi=140)
    print("已写出: %s" % OUTP)


if __name__ == "__main__":
    main()
