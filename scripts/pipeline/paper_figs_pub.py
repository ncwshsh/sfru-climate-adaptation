# -*- coding: utf-8 -*-
"""paper_figs_pub.py —— 生成全部出版级图件（统一配色/字号/300dpi/PDF）

图件清单与论文对应关系见 `03_论文/分析结果汇总_2026-09-24.md` 的第四节。
输出目录：C:/SF_data/tools/report/pub/
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/mnt/c/SF_data/tools")
import matplotlib.pyplot as plt
from pub_style import (set_style, save, add_basemap, PALETTE, STRAIN_COL, GREY)

ROOT = "/mnt/c/SF_data"
REP = os.path.join(ROOT, "tools", "report")
OUT = os.path.join(REP, "pub")
set_style()


def load_all():
    gea = pd.read_csv(os.path.join(REP, "gea_input.tsv"), sep="\t")
    for c in ["lat", "lon", "rate", "raw_depth", "PC1", "PC2", "PC3", "PC4",
              "bio1", "bio4", "bio11", "bio12"]:
        if c in gea.columns:
            gea[c] = pd.to_numeric(gea[c], errors="coerce")
    return gea


# ---------------- Fig 1：采样分布 + 气候空间 ----------------
def fig1(gea):
    fig = plt.figure(figsize=(7.2, 3.4))
    ax1 = fig.add_subplot(121)
    add_basemap(ax1, step=2, extent=(-130, 125, -40, 55))
    for m in ["US", "FL", "BR", "AM", "AF", "CN"]:
        s = gea[gea["module"] == m]
        if len(s):
            ax1.scatter(s["lon"], s["lat"], s=11, c=PALETTE[m], alpha=.9,
                        edgecolors="none", label="%s (%d)" % (m, len(s)), zorder=3)
    ax1.set_xlabel("Longitude"); ax1.set_ylabel("Latitude")
    ax1.set_title("(a) Sampling sites (n = 214)", pad=4)
    ax1.legend(loc="upper left", frameon=False, ncol=2, handletextpad=.3,
               columnspacing=.8, fontsize=6.3, labelspacing=.25)

    ax2 = fig.add_subplot(122)
    for m in ["US", "BR", "AF", "AM", "CN", "FL"]:
        s = gea[gea["module"] == m]
        if len(s):
            ax2.scatter(s["bio1"], s["bio12"], s=11, c=PALETTE[m], alpha=.85,
                        edgecolors="none")
    ax2.set_xlabel("BIO1 annual mean temperature (C)")
    ax2.set_ylabel("BIO12 annual precipitation (mm)")
    ax2.set_title("(b) Climatic space occupied", pad=4)
    save(fig, "Fig1_sampling_and_climate")


# ---------------- Fig 2：群体结构 ----------------
def fig2(gea):
    fig = plt.figure(figsize=(7.2, 3.4))
    ax1 = fig.add_subplot(121)
    for m in ["US", "BR", "AF", "AM", "CN", "FL"]:
        s = gea[gea["module"] == m]
        if len(s):
            ax1.scatter(s["PC1"], s["PC2"], s=11, c=PALETTE[m], alpha=.85,
                        edgecolors="none", label="%s" % m)
    ax1.axhline(0, c="#dddddd", lw=.6); ax1.axvline(0, c="#dddddd", lw=.6)
    ax1.set_xlabel("PC1 (6.61%)"); ax1.set_ylabel("PC2 (3.01%)")
    ax1.set_title("(a) Population structure (PCAngsd)", pad=4)
    ax1.legend(frameon=False, ncol=3, handletextpad=.2, columnspacing=.6)

    us = gea[gea["module"] == "US"]
    ax2 = fig.add_subplot(122)
    sc = ax2.scatter(us["lat"], us["PC1"], s=13, c=us["rate"], cmap="viridis",
                     edgecolors="none")
    ax2.set_xlabel("Latitude (deg)"); ax2.set_ylabel("PC1")
    r = np.corrcoef(us["lat"], us["PC1"])[0, 1]
    ax2.set_title("(b) US module: PC1 vs latitude  (r = %+.3f)" % r, pad=4)
    plt.colorbar(sc, ax=ax2, label="Mapping rate (%)", fraction=.046)
    save(fig, "Fig2_population_structure")


# ---------------- Fig 3：株系格局 ----------------
def fig3(gea):
    fig = plt.figure(figsize=(7.2, 3.4))
    ax1 = fig.add_subplot(121)
    add_basemap(ax1, step=2, extent=(-130, 125, -40, 55))
    for st, lab in [("C", "C (corn)"), ("R", "R (rice)"), ("H", "H (hybrid)")]:
        s = gea[gea["strain"] == st]
        if len(s):
            ax1.scatter(s["lon"], s["lat"], s=11, c=STRAIN_COL[st], alpha=.9,
                        edgecolors="none", label="%s n=%d" % (lab, len(s)), zorder=3)
    ax1.set_xlabel("Longitude"); ax1.set_ylabel("Latitude")
    ax1.set_title("(a) Geographic distribution of host strains", pad=4)
    ax1.legend(loc="upper left", frameon=False, handletextpad=.3, fontsize=6.3)

    ax2 = fig.add_subplot(122)
    mods = ["US", "FL", "BR", "AM", "AF", "CN"]
    c = [int((gea[(gea["module"] == m)]["strain"] == "C").sum()) for m in mods]
    r_ = [int((gea[(gea["module"] == m)]["strain"] == "R").sum()) for m in mods]
    x = np.arange(len(mods))
    ax2.bar(x, c, color=STRAIN_COL["C"], label="C (corn)", width=.62)
    ax2.bar(x, r_, bottom=c, color=STRAIN_COL["R"], label="R (rice)", width=.62)
    for i in range(len(mods)):
        if c[i]: ax2.text(i, c[i] / 2, str(c[i]), ha="center", va="center", color="white", fontsize=7)
        if r_[i]: ax2.text(i, c[i] + r_[i] / 2, str(r_[i]), ha="center", va="center", color="white", fontsize=7)
    ax2.set_xticks(x); ax2.set_xticklabels(mods)
    ax2.set_ylabel("Number of samples")
    ax2.set_title("(b) Strain composition by module", pad=4)
    ax2.legend(frameon=False)
    save(fig, "Fig3_host_strain")


# ---------------- Fig 4：美国气候梯度 ----------------
def fig4(gea):
    us = gea[gea["module"] == "US"].dropna(subset=["lat", "bio1"])
    fig, ax = plt.subplots(figsize=(3.6, 3.4))
    ax.scatter(us["lat"], us["bio1"], s=14, c=STRAIN_COL["C"], alpha=.75,
               edgecolors="none", label="BIO1 annual mean")
    ax.scatter(us["lat"], us["bio11"], s=14, c=STRAIN_COL["R"], alpha=.75,
               edgecolors="none", label="BIO11 coldest quarter")
    r1 = np.corrcoef(us["lat"], us["bio1"])[0, 1]
    r11 = np.corrcoef(us["lat"], us["bio11"])[0, 1]
    ax.axhline(0, c="#dddddd", lw=.6)
    ax.set_xlabel("Latitude (deg)"); ax.set_ylabel("Temperature (C)")
    ax.set_title("US module climate gradient\nr(BIO1)=%+.3f, r(BIO11)=%+.3f" % (r1, r11), pad=4)
    ax.legend(frameon=False, loc="upper right")
    save(fig, "Fig4_US_climate_gradient")


# ---------------- Fig 5：RDA 结果 ----------------
def fig5():
    z = pd.read_csv(os.path.join(REP, "gea_rda_z_full.tsv"), sep="\t")
    zv = z["z"].values.astype(np.float64)
    mk = z["marker"].values
    fig = plt.figure(figsize=(7.2, 2.9))

    # (a) 载荷分布
    ax1 = fig.add_subplot(131)
    ax1.hist(zv, bins=220, color="#9aa0a6")
    for t in (-4, 4):
        ax1.axvline(t, c=STRAIN_COL["C"], ls="--", lw=.9)
    ax1.set_yscale("log")
    ax1.set_xlabel("z of RDA1 loading"); ax1.set_ylabel("Number of SNPs (log)")
    ax1.set_title("(a) Loading distribution", pad=4, fontsize=8)

    # (b) QQ 图（GEA 论文标配：看 p 值是否整体偏离零假设、尾部是否抬起）
    ax2 = fig.add_subplot(132)
    from scipy.stats import norm
    p = 2.0 * norm.sf(np.abs(zv))
    # ⚠️ p 必须**升序**（最显著在前），这样 obs=-log10(p) 与 exp 都是降序、方向一致。
    #    若写成 np.sort(p)[::-1]，obs 会变成小在前，与 exp 反配，QQ 曲线会整个反过来。
    p = np.sort(p)
    n = len(p)
    exp = -np.log10(np.arange(1, n + 1) / (n + 1))
    obs = -np.log10(np.clip(p, 1e-300, 1))
    step = max(1, n // 200000)       # 抽稀绘图点（1600 万点画不动）
    ax2.scatter(exp[::step], obs[::step], s=.8, c="#7f8c8d", edgecolors="none", rasterized=True)
    lim = max(exp.max(), obs.max())
    ax2.plot([0, lim], [0, lim], c=STRAIN_COL["C"], lw=.9, ls="--")
    thr = -np.log10(2 * norm.sf(5.189))
    ax2.axhline(thr, c="#2471a3", lw=.8, ls=":")
    ax2.text(0.06 * lim, thr * 1.04, "FDR 0.05", fontsize=6, color="#2471a3")
    ax2.set_xlabel("Expected -log10(p)"); ax2.set_ylabel("Observed -log10(p)")
    ax2.set_title("(b) QQ plot (tail departure)", pad=4, fontsize=8)

    # (c) Manhattan：标签稀疏（每 5 条标一个数字），避免挤成一团
    ax3 = fig.add_subplot(133)
    chrom = np.array([str(m).rsplit("_", 1)[0] for m in mk])
    pos = np.array([int(str(m).rsplit("_", 1)[1]) for m in mk])
    order = sorted(set(chrom))
    cand_thr = 5.189
    off, ticks, labels = 0, [], []
    for i, c in enumerate(order):
        sel = chrom == c
        ax3.scatter(pos[sel] + off, zv[sel], s=.1, c="#95a5a6", alpha=.3,
                    edgecolors="none", rasterized=True)
        cc = sel & (np.abs(zv) >= cand_thr)
        if cc.any():
            ax3.scatter(pos[cc] + off, zv[cc], s=2.4, c=STRAIN_COL["C"],
                        edgecolors="none", rasterized=True)
        if i % 5 == 0:                       # 每 5 条标一个数字
            ticks.append(off + pos[sel].max() / 2)
            labels.append(str(i + 1))
        off += pos[sel].max() + 2_000_000
    ax3.axhline(0, c="#dddddd", lw=.5)
    ax3.set_xticks(ticks); ax3.set_xticklabels(labels, fontsize=6)
    ax3.set_xlabel("Chromosome"); ax3.set_ylabel("z (RDA1)")
    ax3.set_title("(c) Manhattan plot (n=%d FDR-significant)" % int(cand.sum() if 'cand' in dir() else
                                                                 (np.abs(zv) >= cand_thr).sum()), pad=4, fontsize=8)
    save(fig, "Fig5_RDA_results")


# ---------------- Fig 6：跨国对比 ----------------
def fig6():
    d = pd.read_csv(os.path.join(REP, "crossregion_genes.tsv"), sep="\t")
    cols = ["US-C", "BR-C", "AF-C", "AM-C", "CN-C"]
    gs = np.zeros((len(cols), len(cols)), int)
    for i, a in enumerate(cols):
        for j, b in enumerate(cols):
            k = np.sum((d[a] == 1) & (d[b] == 1))
            gs[i, j] = k
    fig = plt.figure(figsize=(7.2, 3.2))
    ax1 = fig.add_subplot(121)
    im = ax1.imshow(gs, cmap="Reds")
    ax1.set_xticks(range(len(cols))); ax1.set_xticklabels(cols, fontsize=6.5)
    ax1.set_yticks(range(len(cols))); ax1.set_yticklabels(cols, fontsize=6.5)
    for i in range(len(cols)):
        for j in range(len(cols)):
            ax1.text(j, i, str(gs[i, j]), ha="center", va="center", fontsize=6,
                     color="white" if gs[i, j] > gs.max() * .6 else "black")
    ax1.set_title("(a) Shared candidate genes\n(same-threshold per region)", pad=4)
    plt.colorbar(im, ax=ax1, fraction=.046)

    ax2 = fig.add_subplot(122)
    nshare = d["n_region"].values
    vals, cnts = np.unique(nshare, return_counts=True)
    ax2.bar(vals.astype(str), cnts, color="#2471a3", width=.6)
    for v, c in zip(vals, cnts):
        ax2.text(v, c, str(c), ha="center", va="bottom", fontsize=7)
    ax2.set_xlabel("Number of regions sharing the gene")
    ax2.set_ylabel("Number of genes")
    ax2.set_yscale("log")
    ax2.set_title("(b) Sharing across regions", pad=4)
    save(fig, "Fig6_cross_region")


# ---------------- Fig 7：混淆诊断 ----------------
def fig7():
    d = pd.read_csv(os.path.join(REP, "qc_s2_bm2k15.tsv"), sep="\t")
    for c in ["lat", "rate", "raw_depth"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["lat"])
    fig = plt.figure(figsize=(7.2, 2.6))
    ax1 = fig.add_subplot(131)
    for m in ["US", "BR", "AF", "AM", "CN", "FL"]:
        s = d[d["module"] == m]
        if len(s):
            ax1.scatter(s["lat"], s["rate"], s=11, c=PALETTE[m], alpha=.8,
                        edgecolors="none", label=m)
    r = np.corrcoef(d["lat"], d["rate"])[0, 1]
    ax1.set_xlabel("Latitude (deg)"); ax1.set_ylabel("Mapping rate (%)")
    ax1.set_title("(a) All modules: r = %+.3f\n(cross-module effect)" % r, pad=4)
    ax1.legend(frameon=False, ncol=2, handletextpad=.2, columnspacing=.5)

    us = d[d["module"] == "US"]
    ax2 = fig.add_subplot(132)
    ax2.scatter(us["lat"], us["rate"], s=12, c=PALETTE["US"], alpha=.85, edgecolors="none")
    r2 = np.corrcoef(us["lat"], us["rate"])[0, 1]
    ax2.set_xlabel("Latitude (deg)"); ax2.set_ylabel("Mapping rate (%)")
    ax2.set_title("(b) US module: r = %+.3f\n(no within-module confounding)" % r2, pad=4)

    ax3 = fig.add_subplot(133)
    for m in ["US", "BR", "AF", "AM", "CN", "FL"]:
        s = d[d["module"] == m]
        if len(s):
            ax3.scatter(s["lat"], s["raw_depth"], s=11, c=PALETTE[m], alpha=.8, edgecolors="none")
    r3 = np.corrcoef(d["lat"], d["raw_depth"])[0, 1]
    ax3.axhline(6, c=GREY, ls="--", lw=.9)
    ax3.text(-33, 6.6, "target 6x", fontsize=6, color=GREY)
    ax3.set_xlabel("Latitude (deg)"); ax3.set_ylabel("Raw depth (x)")
    ax3.set_title("(c) Depth vs latitude: r = %+.3f\n(not a confounder)" % r3, pad=4)
    save(fig, "Fig7_confounding_diagnostics")


# ---------------- Fig S1：各模块比对率（新补） ----------------
def figS1():
    d = pd.read_csv(os.path.join(REP, "qc_s2_bm2k15.tsv"), sep="\t")
    d["rate"] = pd.to_numeric(d["rate"], errors="coerce")
    mods = ["US", "FL", "BR", "AM", "AF", "CN"]
    data = [d[d["module"] == m]["rate"].dropna().values for m in mods]
    fig, ax = plt.subplots(figsize=(3.6, 3.2))
    bp = ax.boxplot(data, tick_labels=mods, patch_artist=True, widths=.6,
                    medianprops=dict(color="black", lw=1), flierprops=dict(markersize=1.8))
    for b, m in zip(bp["boxes"], mods):
        b.set_facecolor(PALETTE[m]); b.set_alpha(.65); b.set_edgecolor("black"); b.set_linewidth(.6)
    for i, m in enumerate(mods):
        v = data[i]
        ax.scatter(np.random.normal(i + 1, .07, len(v)), v, s=4, c="black", alpha=.35, edgecolors="none")
    ax.axhline(90, c=GREY, ls="--", lw=.9)
    ax.text(0.6, 90.8, "90% reference", fontsize=6, color=GREY)
    ax.set_ylabel("Mapping rate (%)")
    ax.set_title("Mapping rate by module\n(BR suffers reference bias)", pad=4)
    save(fig, "FigS1_mapping_rate")


# ---------------- Fig S2：两法一致性 ----------------
def figS2():
    zr = pd.read_csv(os.path.join(REP, "gea_rda_z_full.tsv"), sep="\t")
    pl = pd.read_csv(os.path.join(REP, "gea_lfmm_p.tsv"), sep="\t")[["marker", "p"]]
    m = pl.merge(zr, on="marker", how="inner")
    x = np.abs(m["z"].values.astype(float))
    y = -np.log10(np.maximum(m["p"].values.astype(float), 1e-300))
    r = np.corrcoef(x, y)[0, 1]
    from scipy.stats import spearmanr
    rho = spearmanr(x, y).correlation
    fig, ax = plt.subplots(figsize=(3.5, 3.2))
    hb = ax.hexbin(x, y, gridsize=70, bins="log", cmap="viridis", mincnt=1)
    ax.set_xlabel("|z| (partial RDA)")
    ax.set_ylabel("-log10(p) (single-SNP F test)")
    ax.set_title("Cross-method concordance\nr=%+.3f, rho=%+.3f (n=%.2fM SNPs)"
                 % (r, rho, len(m) / 1e6), pad=4)
    plt.colorbar(hb, ax=ax, label="log10 count", fraction=.046)
    save(fig, "FigS2_cross_method")


# ---------------- Fig S3：株系判别验证 ----------------
def figS3():
    d = pd.read_csv(os.path.join(REP, "strain_predicted.tsv"), sep="\t")
    us = d[(d["module"] == "US") & (d["strain_known"].isin(["C", "R"]))]
    tab = pd.crosstab(us["strain_known"], us["strain_pred"])
    fig, ax = plt.subplots(figsize=(3.2, 3.0))
    im = ax.imshow(tab.values, cmap="Blues")
    ax.set_xticks(range(tab.shape[1])); ax.set_xticklabels(tab.columns)
    ax.set_yticks(range(tab.shape[0])); ax.set_yticklabels(tab.index)
    for i in range(tab.shape[0]):
        for j in range(tab.shape[1]):
            ax.text(j, i, str(tab.values[i, j]), ha="center", va="center", fontsize=9,
                    color="white" if tab.values[i, j] > tab.values.max() * .6 else "black")
    agree = 100 * np.trace(tab.values) / tab.values.sum()
    ax.set_xlabel("Predicted (Tpi/Flightin)"); ax.set_ylabel("NCBI label")
    ax.set_title("Strain assignment validation\nleave-one-out accuracy 100%% (n=%d)" % tab.values.sum(), pad=4)
    save(fig, "FigS3_strain_validation")


if __name__ == "__main__":
    gea = load_all()
    print("生成出版级图件 → %s" % OUT)
    fig1(gea); fig2(gea); fig3(gea); fig4(gea)
    fig5(); fig6(); fig7(); figS1(); figS2(); figS3()
    print("完成")
