# -*- coding: utf-8 -*-
"""gea_lfmm.py —— 交叉验证：用**单位点线性模型 + 潜在因子**（LFMM 类方法）重跑 GEA

为什么需要这一步：
  RDA 是"多变量约束排序"——把所有位点一起投影到气候轴上，找的是整体格局。
  LFMM 是"单位点回归"——每个位点单独对气候做回归、检验气候系数，同时用
  潜在因子（种群结构）和株系做校正。两者统计路径完全不同，
  若结论一致（同一批模块富集、候选位点高度重叠），可信度才是真的。

★ 说明：官方 lfmm2 二进制在 conda 和 GitHub 上都取不到（2026-09-23 实测），
  因此这里用**等价的向量化实现**：Y ~ 气候 + 株系 + PC(潜在因子)，对气候做 F 检验。
  潜在因子用 PCAngsd 得到的 PC（即 LFMM 里 K 个潜在因子的角色），株系作为显式协变量。
  这与 lfmm2 的模型设定一致，只是因子用 PCA 估计而非 EM 联合估计。

用法: python /mnt/c/SF_data/tools/gea_lfmm.py
"""
import os
import numpy as np
import pandas as pd
from scipy.stats import f as fdist

ROOT = "/mnt/c/SF_data"
BEAGLE = os.path.join(ROOT, "..", "..", "home", "hugo", "data", "angsd", "beagle_1M.beagle.gz")
BEAGLE = "/home/hugo/data/angsd/beagle_1M.beagle.gz"
GEA = os.path.join(ROOT, "tools", "report", "gea_input.tsv")
CLIMT = os.path.join(ROOT, "tools", "report", "climate_s2.tsv")
PCA = "/home/hugo/data/angsd/pca_scores.tsv"
ZFULL = os.path.join(ROOT, "tools", "report", "gea_rda_z_full.tsv")
BAMLIST = os.path.join(ROOT, "tools", "bamlist_keep214.txt")
OUTDIR = os.path.join(ROOT, "tools", "report")


def main():
    # ---- 元数据 ----
    meta = pd.read_csv(GEA, sep="\t")
    runs = [os.path.basename(l.strip()).split(".")[0] for l in open(BAMLIST) if l.strip()]
    meta = meta.set_index("run").loc[runs].reset_index()
    us = np.where(meta["module"].values == "US")[0]
    n = len(us)
    print("美国样本 %d 个" % n)

    # 气候（与 RDA 完全相同的处理，保证可比）
    climt = pd.read_csv(CLIMT, sep="\t").set_index("run")
    bio = ["bio%d" % i for i in range(1, 20)]
    clim = climt.loc[runs, bio].astype(float).values[us]
    cz = (clim - clim.mean(0)) / (clim.std(0) + 1e-9)
    C = np.corrcoef(cz.T)
    keepc = []
    for i in range(C.shape[0]):
        if all(abs(C[i, j]) < 0.9 for j in keepc):
            keepc.append(i)
    cz = cz[:, keepc]
    Uc, Sc, _ = np.linalg.svd(cz - cz.mean(0), full_matrices=False)
    X = Uc[:, :3] * Sc[:3]
    X = (X - X.mean(0)) / (X.std(0) + 1e-9)          # 143 × 3

    # 协变量：株系 + 潜在因子 PC2~4（PC1≈株系，跳过）
    pcs = pd.read_csv(PCA, sep="\t").set_index("run")
    pc234 = pcs.loc[runs, ["PC2", "PC3", "PC4"]].values[us]
    strain = meta["strain"].values[us]
    D0 = np.column_stack([np.ones(n), (strain == "R").astype(float), pc234])   # 143 × 5
    D1 = np.column_stack([D0, X])                                              # 143 × 8（全模型）
    K, P1 = X.shape[1], D1.shape[1]
    print("设计矩阵：D0 %s（截距+株系+PC2~4），D1 %s（+气候 %d 轴）" % (D0.shape, D1.shape, K))

    # ---- 基因型 ----
    print("读基因型 %s …" % BEAGLE)
    df = pd.read_csv(BEAGLE, sep=r"\s+", dtype={0: str})
    gl = df.iloc[:, 3:].values
    Y = (gl[:, 1::3].astype(np.float64) + 2.0 * gl[:, 2::3].astype(np.float64))[:, us]  # 位点×143
    markers = df.iloc[:, 0].values
    print("  位点 %d 个" % Y.shape[0])

    # 去掉单态
    keep = Y.var(axis=1) > 1e-6
    Y, markers = Y[keep], markers[keep]
    M = Y.shape[0]

    # 中心化
    Yc = Y - Y.mean(axis=1, keepdims=True)
    Ytc = Yc.T                       # 143 × M

    def ssr(D):
        """返回每个位点的残差平方和（向量化）"""
        Pinv = np.linalg.pinv(D.T @ D) @ D.T        # p × 143
        beta = Pinv @ Ytc                            # p × M
        return (Ytc ** 2).sum(axis=0) - np.sum(beta * (D.T @ Ytc), axis=0)

    ssr0 = ssr(D0)
    ssr1 = ssr(D1)
    df2 = n - P1
    F = np.maximum(((ssr0 - ssr1) / K) / (np.maximum(ssr1, 1e-12) / df2), 0)
    p = fdist.sf(F, K, df2)
    print("F 检验完成：df1=%d, df2=%d" % (K, df2))

    # ---- FDR ----
    def bh(pv, alpha=0.05):
        m = len(pv)
        o = np.argsort(pv); ps = pv[o]
        passed = ps <= alpha * (np.arange(1, m + 1) / m)
        if not passed.any():
            return np.zeros(m, bool), 0.0
        cut = ps[int(np.where(passed)[0].max())]
        return pv <= cut, cut

    sig, cut = bh(p)
    print()
    print("=== LFMM 类单位点检验 ===")
    print("  位点 %d 个；FDR<0.05 显著 %d 个（p 阈值 %.3e）" % (M, sig.sum(), cut))

    # ---- 与 RDA 的交叉验证 ----
    print()
    print("=== 与 RDA 的交叉验证 ===")
    zf = pd.read_csv(ZFULL, sep="\t")
    zmap = dict(zip(zf["marker"].astype(str), zf["z"].astype(float)))
    common = [m for m in markers if str(m) in zmap]
    idx = np.array([i for i, m in enumerate(markers) if str(m) in zmap])
    zr = np.array([zmap[str(markers[i])] for i in idx])
    pl = p[idx]
    nl = -np.log10(np.maximum(pl, 1e-300))
    azr = np.abs(zr)
    r_pear = float(np.corrcoef(azr, nl)[0, 1])
    # Spearman（秩相关，更稳）
    from scipy.stats import spearmanr
    r_spear = float(spearmanr(azr, nl).correlation)
    print("  共同位点 %d 个" % len(idx))
    print("  |z_RDA| 与 -log10(p_LFMM) 相关：Pearson r = %+.3f   Spearman ρ = %+.3f" % (r_pear, r_spear))

    # RDA 的 69 个 FDR 显著位点中有多少在 LFMM 下也显著（或排名靠前）
    sigl_set = set(np.where(sig)[0].tolist())
    # RDA 显著位点在本位点集里的
    zcand = np.where(np.abs(zr) >= 5.189)[0]      # RDA 的 FDR 阈值
    hit = sum(1 for i in zcand if idx[i] in sigl_set)
    print("  RDA 的 FDR 显著位点在本位点集中有 %d 个，其中 %d 个在 LFMM 下也通过 FDR" % (len(zcand), hit))
    if len(zcand):
        # 它们在 LFMM p 值上的分位
        qs = [float((nl < nl[i]).mean()) for i in zcand]
        # ⚠️ 字符串里的 "100%" 必须写成 "100%%"，否则被当成格式占位符导致 print 崩溃
        print("  这些位点在 LFMM 的 -log10(p) 上平均处于 %.1f%% 分位（越接近 100%% 越一致）"
              % (100 * np.mean(qs)))

    # 两种方法的 top 位点重叠
    top_r = set(idx[np.argsort(-np.abs(zr))[:1000]].tolist())
    top_l = set(np.argsort(pl)[:1000].tolist())
    ov = len(top_r & top_l)
    print("  各自 top 1000 位点的重叠：%d 个（随机期望 %.0f 个）"
          % (ov, 1000 * 1000 / len(idx)))

    # ---- 输出 ----
    out = os.path.join(OUTDIR, "gea_lfmm_p.tsv")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("marker\tF\tp\n")
        fh.writelines("%s\t%.4f\t%.4e\n" % (markers[i], F[i], p[i]) for i in range(M))
    print()
    print("已写出: %s" % out)

    outs = os.path.join(OUTDIR, "gea_lfmm_significant.tsv")
    with open(outs, "w", encoding="utf-8") as fh:
        fh.write("marker\tp\n")
        for i in np.where(sig)[0]:
            fh.write("%s\t%.4e\n" % (markers[i], p[i]))
    print("已写出: %s（%d 个）" % (outs, sig.sum()))


if __name__ == "__main__":
    main()
