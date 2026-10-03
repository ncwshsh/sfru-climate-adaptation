# -*- coding: utf-8 -*-
"""gea_rda_full.py —— 用**全量 1,623 万位点**重跑 partial RDA（提升统计功效）

为什么分块流式：
  全量矩阵 = 16,230,602 位点 × 645 列，float64 需要 84 GB，内存装不下。
  但 RDA 的核心只需要 **Gram 矩阵 G = Yr'Yr（143×143）** 和 **位点载荷**，
  两者都能分块累加 ⇒ 一块一块读，内存只占几 MB。

两遍：
  Pass 1：读 beagle → 期望剂量 → 对条件变量取残差 → 累积 G、写 Yr(float32) 到磁盘、记方差
  Pass 2：由 G 求帽子矩阵 H → 读 Yr 分块算载荷 → z 分数 → 候选位点

用法: python /mnt/c/SF_data/tools/gea_rda_full.py [块大小]
"""
import os
import sys
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/mnt/c/SF_data"
BEAGLE = "/home/hugo/data/angsd/s2_gl.beagle.gz"        # 全量 6.5 GB
YRFILE = "/home/hugo/data/angsd/Yr_US.f32"              # 中间文件（float32）
GEA = os.path.join(ROOT, "tools", "report", "gea_input.tsv")
CLIMT = os.path.join(ROOT, "tools", "report", "climate_s2.tsv")
PCA = "/home/hugo/data/angsd/pca_scores.tsv"
BAMLIST = os.path.join(ROOT, "tools", "bamlist_keep214.txt")
OUTDIR = os.path.join(ROOT, "tools", "report")

CHUNK = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
NPERM = 999
SEED = 20260923
MOD = "US"


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def main():
    t0 = time.time()
    # ---------- 元数据 ----------
    meta = pd.read_csv(GEA, sep="\t")
    runs = [os.path.basename(l.strip()).split(".")[0]
            for l in open(BAMLIST) if l.strip()]
    meta = meta.set_index("run").loc[runs].reset_index()
    us_idx = np.where(meta["module"].values == MOD)[0]
    n = len(us_idx)
    log("队列 %d 个，%s 模块 %d 个" % (len(runs), MOD, n))

    climt = pd.read_csv(CLIMT, sep="\t").set_index("run")
    bio_cols = ["bio%d" % i for i in range(1, 20)]
    clim = climt.loc[runs, bio_cols].astype(float).values[us_idx]

    pcs = pd.read_csv(PCA, sep="\t").set_index("run")
    pc234 = pcs.loc[runs, ["PC2", "PC3", "PC4"]].values[us_idx]
    strain = meta["strain"].values[us_idx]
    is_r = (strain == "R").astype(float)
    has_s = (strain != "").astype(float)
    Z = np.column_stack([np.ones(n), is_r, has_s, pc234])
    Z = Z[:, Z.std(0) > 1e-9]
    Zc = Z - Z.mean(0)
    log("条件变量 Z: %s" % str(Z.shape))

    # 气候去共线 + PCA（同抽稀版）
    cz = (clim - clim.mean(0)) / (clim.std(0) + 1e-9)
    C = np.corrcoef(cz.T)
    keepc = []
    for i in range(C.shape[0]):
        if all(abs(C[i, j]) < 0.9 for j in keepc):
            keepc.append(i)
    cz = cz[:, keepc]
    Uc, Sc, Vc = np.linalg.svd(cz - cz.mean(0), full_matrices=False)
    PCclim = Uc[:, :3] * Sc[:3]
    log("气候去共线后 %d 个变量 → PCA 前 3 轴（%s%%）"
        % (len(keepc), np.round(100 * (Sc ** 2 / (Sc ** 2).sum())[:3], 1)))

    def resid(A):
        A = A - A.mean(0)
        beta, *_ = np.linalg.lstsq(Zc, A, rcond=None)
        return A - Zc @ beta

    Xr = resid(PCclim)
    Xr = (Xr - Xr.mean(0)) / (Xr.std(0) + 1e-9)

    # ---------- Pass 1 ----------
    log("Pass 1：流式读全量 beagle（块 %d 行）…" % CHUNK)
    G = np.zeros((n, n))
    markers = []
    vars_ = []
    n_sites = 0
    with open(YRFILE, "wb") as fout:
        reader = pd.read_csv(BEAGLE, sep=r"\s+", dtype={0: str}, chunksize=CHUNK)
        for j, df in enumerate(reader, 1):
            gl = df.iloc[:, 3:].values
            Yb = (gl[:, 1::3].astype(np.float64) + 2.0 * gl[:, 2::3].astype(np.float64))
            Yb = Yb[:, us_idx]                       # 位点 × 143
            Ybc = Yb - Yb.mean(axis=1, keepdims=True)
            beta, *_ = np.linalg.lstsq(Zc, Ybc.T, rcond=None)
            Yr = Ybc - (Zc @ beta).T                 # 位点 × 143
            G += Yr.T @ Yr
            Yr.astype(np.float32).tofile(fout)
            vars_.append(Yr.var(axis=1))
            markers.extend(df.iloc[:, 0].tolist())
            n_sites += Yr.shape[0]
            if j % 40 == 0:
                log("  %d 块 / %d 位点（%.0f 秒）" % (j, n_sites, time.time() - t0))
    markers = np.array(markers)
    vars_ = np.concatenate(vars_)
    log("Pass 1 完成：%d 位点，用时 %.0f 秒" % (n_sites, time.time() - t0))

    keep = vars_ > 1e-6
    log("  去掉单态位点：保留 %d 个" % keep.sum())

    # ---------- RDA ----------
    XtX_inv = np.linalg.pinv(Xr.T @ Xr)
    P = Xr @ XtX_inv @ Xr.T
    inertia = float(np.trace(P @ G))
    tot = float(np.trace(G))
    r2 = inertia / tot
    log("partial RDA: R² = %.4f (%.2f%%)" % (r2, 100 * r2))

    rng = np.random.default_rng(SEED)
    cnt = 0
    for _ in range(NPERM):
        idx = rng.permutation(n)
        if float(np.trace(Xr[idx] @ XtX_inv @ Xr[idx].T @ G)) >= inertia:
            cnt += 1
    pval = (cnt + 1) / (NPERM + 1)
    log("置换检验 %d 次: p = %.4f" % (NPERM, pval))

    # ---------- 位点载荷（Pass 2）----------
    Gy = P @ G @ P
    w, v = np.linalg.eigh(Gy)
    o = np.argsort(w)[::-1]
    w, v = w[o], v[:, o]
    k = min(3, int((w > 1e-12).sum()))
    U, S = v[:, :k], np.sqrt(np.maximum(w[:k], 0))
    A = P @ U                                  # 143 × k

    log("Pass 2：读回 Yr 算载荷（%d 位点）…" % keep.sum())
    loads = np.zeros((keep.sum(), k), dtype=np.float32)
    rowsize = n * 4
    kept_i = np.where(keep)[0]
    with open(YRFILE, "rb") as fin:
        pos_in_file = 0
        buf_start = 0
        while True:
            blk = np.fromfile(fin, dtype=np.float32, count=CHUNK * n)
            if blk.size == 0:
                break
            nrow = blk.size // n
            blk = blk.reshape(nrow, n)
            gi = np.arange(buf_start, buf_start + nrow)
            buf_start += nrow
            sel = np.isin(gi, kept_i)
            if sel.any():
                tgt = np.searchsorted(kept_i, gi[sel])
                loads[tgt] = (blk[sel] @ A / S).astype(np.float32)
    log("  载荷计算完成（%.0f 秒）" % (time.time() - t0))

    z1 = loads[:, 0].astype(np.float64)
    z1 = (z1 - z1.mean()) / (z1.std() + 1e-12)
    for kk in range(k):
        zz = loads[:, kk].astype(np.float64)
        zz = (zz - zz.mean()) / (zz.std() + 1e-12)
        if kk == 0:
            z1 = zz

    cand = np.abs(z1) > 4
    log("候选位点（|z|>4）: %d 个" % cand.sum())

    # 存盘
    kept_markers = markers[keep]
    with open(os.path.join(OUTDIR, "gea_rda_z_full.tsv"), "w", encoding="utf-8") as fh:
        fh.write("marker\tz\n")
        fh.writelines("%s\t%.4f\n" % (kept_markers[i], z1[i]) for i in range(len(z1)))

    maf = None
    with open(os.path.join(OUTDIR, "gea_candidates_full.tsv"), "w", encoding="utf-8") as fh:
        fh.write("marker\tchrom\tpos\tz\n")
        for i in np.where(cand)[0]:
            mk = str(kept_markers[i])
            c, p = mk.rsplit("_", 1)
            fh.write("%s\t%s\t%s\t%.3f\n" % (mk, c, p, z1[i]))
    log("已写出候选位点表与 z 表")

    # ---------- 画图 ----------
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))
    score = U * S
    lat = meta["lat"].values[us_idx].astype(float)
    sc = ax[0].scatter(score[:, 0], score[:, 1] if k > 1 else np.zeros(n),
                       c=lat, cmap="coolwarm", s=28, edgecolors="none")
    ax[0].set_xlabel("RDA1"); ax[0].set_ylabel("RDA2")
    ax[0].set_title("partial RDA, US n=%d, %d SNPs\nR²=%.3f, p=%.4f"
                    % (n, keep.sum(), r2, pval), fontsize=11)
    plt.colorbar(sc, ax=ax[0], label="Latitude")

    ax[1].hist(z1, bins=300, color="#888888")
    ax[1].axvline(4, color="#c0392b", ls="--"); ax[1].axvline(-4, color="#c0392b", ls="--")
    ax[1].set_xlabel("z (RDA1 loading)"); ax[1].set_ylabel("SNPs")
    ax[1].set_title("Full-genome: %d candidates (|z|>4)" % cand.sum(), fontsize=11)

    chrom = np.array([str(m).rsplit("_", 1)[0] for m in kept_markers[cand]])
    order = sorted(set(chrom)); xi = {c: i for i, c in enumerate(order)}
    xs = np.array([xi[c] for c in chrom]) if len(chrom) else np.array([])
    if len(xs):
        ax[2].scatter(xs + rng.normal(0, .12, len(xs)), np.abs(z1[cand]),
                      s=6, alpha=.5, c="#2980b9", edgecolors="none")
        ax[2].set_xticks(range(len(order)))
        ax[2].set_xticklabels([c.replace("NC_", "") for c in order], rotation=90, fontsize=6)
    ax[2].set_xlabel("Chromosome"); ax[2].set_ylabel("|z|")
    ax[2].set_title("Candidates across chromosomes", fontsize=11)

    plt.tight_layout()
    outp = os.path.join(OUTDIR, "gea_rda_US_full.png")
    plt.savefig(outp, dpi=140)
    log("已写出: %s" % outp)
    log("总用时 %.0f 秒" % (time.time() - t0))


if __name__ == "__main__":
    main()
