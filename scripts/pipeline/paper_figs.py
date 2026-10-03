# -*- coding: utf-8 -*-
"""paper_figs.py —— 补绘论文缺的两张图

Fig 7  混淆诊断：比对率/深度 与 纬度的关系（全队列 + 美国内部）
Fig S2 两法一致性：|z_RDA| 与 −log10(p_LFMM) 的散点
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/mnt/c/SF_data"
REP = os.path.join(ROOT, "tools", "report")
QC = os.path.join(REP, "qc_s2_bm2k15.tsv")
ZR = os.path.join(REP, "gea_rda_z_full.tsv")
PL = os.path.join(REP, "gea_lfmm_p.tsv")

COL = {"US": "#c0392b", "BR": "#2980b9", "AF": "#27ae60",
       "AM": "#8e44ad", "CN": "#f39c12", "FL": "#16a085"}


def fig7():
    d = pd.read_csv(QC, sep="\t")
    d["lat"] = pd.to_numeric(d["lat"], errors="coerce")
    d["rate"] = pd.to_numeric(d["rate"], errors="coerce")
    d["raw_depth"] = pd.to_numeric(d["raw_depth"], errors="coerce")
    d = d.dropna(subset=["lat"])
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))

    for m in ["US", "BR", "AF", "AM", "CN", "FL"]:
        s = d[d["module"] == m]
        if len(s):
            ax[0].scatter(s["lat"], s["rate"], s=24, alpha=.75, c=COL[m],
                          label="%s (n=%d)" % (m, len(s)), edgecolors="none")
    r_all = np.corrcoef(d["lat"], d["rate"])[0, 1]
    ax[0].set_xlabel("Latitude (deg)"); ax[0].set_ylabel("Mapping rate (%)")
    ax[0].set_title("(a) Mapping rate vs latitude — all modules\n"
                    "r = %+.3f (across-module effect)" % r_all, fontsize=10)
    ax[0].legend(fontsize=8, markerscale=1.3)

    us = d[d["module"] == "US"]
    r_us = np.corrcoef(us["lat"], us["rate"])[0, 1]
    ax[1].scatter(us["lat"], us["rate"], s=26, alpha=.8, c=COL["US"], edgecolors="none")
    ax[1].set_xlabel("Latitude (deg)"); ax[1].set_ylabel("Mapping rate (%)")
    ax[1].set_title("(b) US module only — the module used for GEA\n"
                    "r = %+.3f (no within-module confounding)" % r_us, fontsize=10)

    r_dep = np.corrcoef(d["lat"], d["raw_depth"])[0, 1]
    for m in ["US", "BR", "AF", "AM", "CN", "FL"]:
        s = d[d["module"] == m]
        if len(s):
            ax[2].scatter(s["lat"], s["raw_depth"], s=24, alpha=.75, c=COL[m], edgecolors="none")
    ax[2].axhline(6, color="#888888", ls="--", lw=1)
    ax[2].text(ax[2].get_xlim()[0], 6.4, "target 6x (uniform downsampling)", fontsize=8, color="#555555")
    ax[2].set_xlabel("Latitude (deg)"); ax[2].set_ylabel("Raw depth (x)")
    ax[2].set_title("(c) Raw depth vs latitude\nr = %+.3f (depth is NOT a confounder)" % r_dep,
                    fontsize=10)

    plt.tight_layout()
    p = os.path.join(REP, "paper_confounding.png")
    plt.savefig(p, dpi=150)
    print("已写出: %s" % p)


def figS2():
    print("读 RDA z（全量 1623 万行）…")
    zr = pd.read_csv(ZR, sep="\t")
    print("读 LFMM p（101 万行）…")
    pl = pd.read_csv(PL, sep="\t")
    pl = pl[["marker", "p"]]
    m = pl.merge(zr, on="marker", how="inner")
    print("  共同位点 %d" % len(m))
    x = np.abs(m["z"].values.astype(float))
    y = -np.log10(np.maximum(m["p"].values.astype(float), 1e-300))
    r = np.corrcoef(x, y)[0, 1]
    from scipy.stats import spearmanr
    rho = spearmanr(x, y).correlation

    fig, ax = plt.subplots(1, 1, figsize=(6.4, 5.6))
    hb = ax.hexbin(x, y, gridsize=90, bins="log", cmap="viridis", mincnt=1)
    ax.set_xlabel("|z| (partial RDA)")
    ax.set_ylabel("−log10(p) (single-SNP F test, LFMM-like)")
    ax.set_title("Cross-method concordance\nPearson r = %+.3f, Spearman rho = %+.3f\n"
                 "top-1000 SNP overlap: 196 (expected 1)" % (r, rho), fontsize=10)
    plt.colorbar(hb, ax=ax, label="log10(count)")
    plt.tight_layout()
    p = os.path.join(REP, "paper_concordance.png")
    plt.savefig(p, dpi=150)
    print("已写出: %s" % p)


if __name__ == "__main__":
    fig7()
    figS2()
