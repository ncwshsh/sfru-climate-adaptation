# -*- coding: utf-8 -*-
"""gea_rda.py —— 个体级基因型-环境关联分析（partial RDA），美国模块

科学问题：美国 143 个样本跨 18.1°~40.9° 纬度、年均温 6.2~24.4℃，
          哪些基因组位点与气候变量显著关联（即气候适应的候选靶点）？

方法：
  1. 基因型 = ANGSD 基因型似然的**期望剂量**（0/1/2 的连续值），
     不硬叫基因型——6x 深度下硬叫会把不确定度当成确定，制造假结构
  2. 环境 = WorldClim BIO1~19 → 标准化后 PCA（19 个变量高度共线，必须降维）
  3. **partial RDA**：先把株系（玉米型/水稻型）和种群结构 PC 作为条件变量回归掉，
     再看剩余的气候部分能解释多少遗传变异
     ——不控制株系的话，找到的"气候基因"很可能只是"株系标记"
  4. 显著性 = 999 次置换检验（打乱样本与气候的对应关系）

计算技巧（n=143 << p=20万）：
  RDA 的 inertia 可用样本间 Gram 矩阵 G = Y Y'（143×143）算，
  置换检验每次只需 143×143 的矩阵运算，极快。

用法（WSL gea 环境）:
  python /mnt/c/SF_data/tools/gea_rda.py
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/mnt/c/SF_data"
BEAGLE = "/home/hugo/data/angsd/beagle_200k.beagle.gz"
GEA = os.path.join(ROOT, "tools", "report", "gea_input.tsv")
PCA = "/home/hugo/data/angsd/pca_scores.tsv"
BAMLIST = os.path.join(ROOT, "tools", "bamlist_keep214.txt")
OUTDIR = os.path.join(ROOT, "tools", "report")
NPERM = 999
SEED = 20260923

MOD = "US"          # 只做美国模块（唯一同时具备：真实梯度 + 高精度坐标 + 株系标注）


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    rng = np.random.default_rng(SEED)

    # ---------- 1. 元数据 ----------
    meta = pd.read_csv(GEA, sep="\t")
    runs = [os.path.basename(l.strip()).split(".")[0]
            for l in open(BAMLIST) if l.strip()]
    meta = meta.set_index("run").loc[runs].reset_index()
    us_idx = np.where(meta["module"].values == MOD)[0]
    print("队列样本 %d 个；其中 %s 模块 %d 个" % (len(runs), MOD, len(us_idx)))

    strain = meta["strain"].values
    # 种群结构协变量：PC2~PC4（PC1 ≈ 株系，会被共线吃掉，故不重复放）
    pcs = pd.read_csv(PCA, sep="\t").set_index("run")
    pc2_4 = pcs.loc[runs, ["PC2", "PC3", "PC4"]].values

    bio_cols = ["bio%d" % i for i in range(1, 20)]
    # ⚠️ gea_input.tsv 只放了 5 个常用 BIO（其余压在 bio_all_json 里），
    #    完整的 19 个变量在 climate_s2.tsv，直接从那里读
    CLIMT = os.path.join(ROOT, "tools", "report", "climate_s2.tsv")
    climt = pd.read_csv(CLIMT, sep="\t").set_index("run")
    clim_all = climt.loc[runs, bio_cols].astype(float).values

    # ---------- 2. 读基因型 ----------
    print("读取基因型（%s）…" % BEAGLE)
    # ⚠️ 第 1 列是 marker 名（字符串），不能用全局 float32 dtype
    df = pd.read_csv(BEAGLE, sep=r"\s+", dtype={0: str}, comment=None)
    print("  位点 %d 个，列 %d 个" % (df.shape[0], df.shape[1]))
    gl = df.iloc[:, 3:].values          # 去掉 marker/allele1/allele2
    n_ind = gl.shape[1] // 3
    assert n_ind == len(runs), "基因型个体数 %d 与队列 %d 不符" % (n_ind, len(runs))
    pos = df.iloc[:, 0].values          # 位点名 chr_pos

    # 期望剂量 GL: (hom_ref, het, hom_alt) -> 0,1,2
    p_hom_ref = gl[:, 0::3].astype(np.float64)
    p_het = gl[:, 1::3].astype(np.float64)
    p_alt = gl[:, 2::3].astype(np.float64)
    del gl
    Y_full = (p_het + 2.0 * p_alt)      # 位点 × 个体
    del p_hom_ref, p_het, p_alt

    # ---------- 3. 美国子集 ----------
    Y = Y_full[:, us_idx]               # 位点 × 143
    del Y_full
    clim = clim_all[us_idx]
    strain_us = strain[us_idx]
    pc_us = pc2_4[us_idx]
    n = Y.shape[1]

    # 去掉单态位点（方差过小）
    v = Y.var(axis=1)
    keep = v > 1e-6
    Y = Y[keep]
    pos = pos[keep]
    print("  去掉单态位点后: %d 个" % Y.shape[0])

    # ---------- 4. 气候降维 ----------
    cz = (clim - clim.mean(0)) / (clim.std(0) + 1e-9)
    # 相关筛选去共线（|r| > 0.9 的只留一个）
    C = np.corrcoef(cz.T)
    keepc = []
    for i in range(C.shape[0]):
        if all(abs(C[i, j]) < 0.9 for j in keepc):
            keepc.append(i)
    cz = cz[:, keepc]
    print("  气候变量去共线后保留 %d 个: %s" % (len(keepc), [bio_cols[i] for i in keepc]))
    # PCA
    Uc, Sc, Vc = np.linalg.svd(cz - cz.mean(0), full_matrices=False)
    PCclim = Uc[:, :3] * Sc[:3]
    ev = (Sc ** 2 / (Sc ** 2).sum())[:3]
    print("  气候 PCA 前 3 轴解释: %s" % np.round(100 * ev, 1))

    # ---------- 5. 条件变量（株系 + 结构）----------
    is_r = (strain_us == "R").astype(float)
    has_s = (strain_us != "").astype(float)
    Z = np.column_stack([np.ones(n), is_r, has_s, pc_us])
    # 去掉常数列
    Z = Z[:, Z.std(0) > 1e-9]
    print("  条件变量矩阵 Z: %s" % str(Z.shape))

    def resid(A, Z):
        """对 Z 做回归取残差（按列中心化后最小二乘）"""
        A = A - A.mean(0)
        Zc = Z - Z.mean(0)
        beta, *_ = np.linalg.lstsq(Zc, A, rcond=None)
        return A - Zc @ beta

    Yr = resid(Y.T, Z).T          # 位点 × 样本（对条件变量取残差）
    Xr = resid(PCclim, Z)         # 气候（对条件变量取残差）
    Xr = (Xr - Xr.mean(0)) / (Xr.std(0) + 1e-9)

    # ---------- 6. partial RDA ----------
    G = Yr.T @ Yr                 # 143×143 Gram
    XtX_inv = np.linalg.pinv(Xr.T @ Xr)
    P = Xr @ XtX_inv @ Xr.T       # 投影矩阵
    inertia = float(np.trace(P @ G))
    tot = float(np.trace(G))
    r2 = inertia / tot
    print()
    print("=== partial RDA（条件：株系 + PC2~4）===")
    print("  气候解释的遗传变异 R² = %.4f （%.2f%%）" % (r2, 100 * r2))

    # 置换检验
    cnt = 0
    for _ in range(NPERM):
        idx = rng.permutation(n)
        Pp = Xr[idx] @ XtX_inv @ Xr[idx].T
        if float(np.trace(Pp @ G)) >= inertia:
            cnt += 1
    pval = (cnt + 1) / (NPERM + 1)
    print("  置换检验 %d 次: p = %.4f" % (NPERM, pval))

    # ---------- 7. 位点载荷与候选位点 ----------
    H = P
    Yhat = H @ Yr.T                     # 143 × 位点（拟合值）
    # 对 Yhat 做 PCA：用 Yhat Yhat' 求样本轴
    Gy = Yhat @ Yhat.T
    w, v = np.linalg.eigh(Gy)
    order = np.argsort(w)[::-1]
    w = w[order]; v = v[:, order]
    k = min(3, (w > 1e-12).sum())
    U = v[:, :k]
    S = np.sqrt(np.maximum(w[:k], 0))
    # 位点载荷 = Yhat' U / S
    load = (Yhat.T @ U) / S             # 位点 × k

    # 每个位点在 RDA1 上的标准化载荷 → z 分数
    z1 = (load[:, 0] - load[:, 0].mean()) / (load[:, 0].std() + 1e-12)
    cand = np.abs(z1) > 4
    print()
    print("=== 候选气候关联位点（|z(RDA1)| > 4）===")
    print("  候选位点数: %d / %d" % (cand.sum(), len(z1)))

    # 全部位点的 z（供功能模块富集检验用）
    with open(os.path.join(OUTDIR, "gea_rda_z.tsv"), "w", encoding="utf-8") as fh:
        fh.write("marker\tz\n")
        fh.writelines("%s\t%.4f\n" % (pos[i], z1[i]) for i in range(len(z1)))

    # 输出候选位点
    chrom = np.array([str(p).rsplit("_", 1)[0] for p in pos])
    outc = os.path.join(OUTDIR, "gea_candidates.tsv")
    with open(outc, "w", encoding="utf-8") as fh:
        fh.write("marker\tchrom\tpos\tRDA1_loading\tz\tmaf_est\n")
        maf = np.minimum(Y.mean(1), 2 - Y.mean(1)) / 2.0
        for i in np.where(cand)[0]:
            fh.write("%s\t%s\t%s\t%.5f\t%.2f\t%.3f\n"
                     % (pos[i], chrom[i], str(pos[i]).rsplit("_", 1)[-1],
                        load[i, 0], z1[i], maf[i]))
    print("  已写出: %s" % outc)

    # 候选位点的染色体分布
    cc = pd.Series(chrom[cand]).value_counts()
    print()
    print("=== 候选位点在染色体上的分布（前 8）===")
    for c, k2 in cc.head(8).items():
        print("  %-14s %d" % (c, k2))

    # ---------- 8. 画图 ----------
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))

    # RDA 排序图：样本得分按纬度着色
    score = U * S                        # 143 × k
    lat = meta["lat"].values[us_idx].astype(float)
    sc = ax[0].scatter(score[:, 0], score[:, 1] if k > 1 else np.zeros(n),
                       c=lat, cmap="coolwarm", s=28, edgecolors="none")
    ax[0].set_xlabel("RDA1")
    ax[0].set_ylabel("RDA2")
    ax[0].set_title("partial RDA (US, n=%d)\nR²=%.3f, p=%.3f" % (n, r2, pval), fontsize=11)
    plt.colorbar(sc, ax=ax[0], label="Latitude")

    # 载荷分布
    ax[1].hist(z1, bins=200, color="#888888")
    ax[1].axvline(4, color="#c0392b", ls="--")
    ax[1].axvline(-4, color="#c0392b", ls="--")
    ax[1].set_xlabel("z score of RDA1 loading")
    ax[1].set_ylabel("Number of SNPs")
    ax[1].set_title("RDA1 loading distribution\n(%d candidates beyond |z|>4)" % cand.sum(), fontsize=11)

    # 候选位点沿基因组分布
    order_c = sorted(set(chrom))
    xi = {c: i for i, c in enumerate(order_c)}
    xs = np.array([xi[c] for c in chrom[cand]]) if cand.sum() else np.array([])
    if len(xs):
        ax[2].scatter(xs + rng.normal(0, .12, len(xs)), np.abs(z1[cand]),
                      s=8, alpha=.6, c="#2980b9", edgecolors="none")
        ax[2].set_xticks(range(len(order_c)))
        ax[2].set_xticklabels([c.replace("NC_", "") for c in order_c], rotation=90, fontsize=6)
    ax[2].set_xlabel("Chromosome")
    ax[2].set_ylabel("|z| of RDA1 loading")
    ax[2].set_title("Candidate SNPs across chromosomes", fontsize=11)

    plt.tight_layout()
    outp = os.path.join(OUTDIR, "gea_rda_US.png")
    plt.savefig(outp, dpi=140)
    print()
    print("已写出: %s" % outp)


if __name__ == "__main__":
    main()
