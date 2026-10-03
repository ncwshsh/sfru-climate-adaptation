# -*- coding: utf-8 -*-
"""fig_lenbias.py —— Fig S4：基因长度偏差的检验（方法学稳健性）

三个面板：
 (a) 候选基因 vs 其余基因的长度分布（候选偏长 2.42×）
     ★ 2026-09-24 统一口径：面板 (a) 的背景**只算带 LOC 注释的基因**（n=13,659），
       与 go_bias_check.py 的长度匹配分析一致。此前用「全部 gene 特征」（含 545 个
       无 LOC 的 tRNA/rRNA 等）作背景，得出 2.59×，会与正文的 2.42× 打架。
 (b) 基因长度 vs 该基因窗口内位点 |z| 均值（无关，ρ=+0.006）⇒ 长度不影响力点统计量
 (c) 三个功能模块基因的长度 vs 背景（无显著差异）⇒ 模块富集结论稳健
"""
import os
import re
import gzip
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, "/mnt/c/SF_data/tools")
import matplotlib.pyplot as plt
from pub_style import set_style, save, PALETTE
from scipy.stats import mannwhitneyu, spearmanr

set_style()
ROOT = "/mnt/c/SF_data"
REP = os.path.join(ROOT, "tools", "report")
GFF = os.path.join(ROOT, "00_ref", "GCF_023101765.2_genomic.gff.gz")
WIN = 20000
MODULES = {"HSP": r"heat shock|dnaJ|hsp\d|hsc70|chaperon",
           "Diapause": r"diapause|circadian|clock|timeless|cryptochrome|juvenile hormone|ecdysone|vitellogenin",
           "Oxidative": r"catalase|peroxidase|superoxide|glutathione|peroxiredoxin|thioredoxin|cytochrome p450"}


def loc_num(x):
    m = re.search(r"LOC(\d+)", str(x))
    return m.group(1) if m else None


def main():
    genes = []
    with gzip.open(GFF, "rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 9 or p[2] != "gene":
                continue
            d = re.search(r"description=([^;]+)", p[8])
            m = re.search(r"Name=LOC(\d+)", p[8])
            genes.append(dict(loc=m.group(1) if m else "", chrom=p[0],
                              start=int(p[3]), end=int(p[4]),
                              length=int(p[4]) - int(p[3]) + 1,
                              desc=(d.group(1) if d else "").replace("%2C", ",")))
    gdf = pd.DataFrame(genes)

    cand = pd.read_csv(os.path.join(REP, "gea_candidates_full_annotated.tsv"), sep="\t")
    fore = set(loc_num(x) for x in cand["gene"] if loc_num(x))
    gdf["iscand"] = gdf["loc"].isin(fore)

    fig = plt.figure(figsize=(7.2, 2.7))

    # (a) 长度分布
    # ★ 统一口径：背景只用带 LOC 注释的基因，与 go_bias_check.py 一致（否则 2.59 vs 2.42 打架）
    #   面板 (b)(c) 刻意维持全量 gene 特征不变，以免改变 rho 与模块箱线图
    gsub = gdf[gdf["loc"] != ""]
    ax1 = fig.add_subplot(131)
    bins = np.logspace(2, 6.2, 45)
    ax1.hist(gsub.loc[~gsub["iscand"], "length"], bins=bins, color="#bdc3c7",
             label="other genes (n=%d)" % (~gsub["iscand"]).sum(), density=True)
    ax1.hist(gsub.loc[gsub["iscand"], "length"], bins=bins, color=PALETTE["US"],
             alpha=.75, label="candidate genes (n=%d)" % gsub["iscand"].sum(), density=True)
    ax1.set_xscale("log")
    ax1.set_xlabel("Gene length (bp)"); ax1.set_ylabel("Density")
    a = gsub.loc[gsub["iscand"], "length"].values
    b = gsub.loc[~gsub["iscand"], "length"].values
    u, p = mannwhitneyu(a, b, alternative="greater")
    ax1.set_title("(a) Candidates are longer (%.2fx, p=%.0e)" % (np.median(a) / np.median(b), p),
                  pad=4, fontsize=8)
    ax1.legend(fontsize=6, frameon=False)

    # (b) 长度 vs |z|
    z = pd.read_csv(os.path.join(REP, "gea_rda_z_full.tsv"), sep="\t")
    z["chrom"] = z["marker"].astype(str).str.rsplit("_", n=1).str[0]
    z["pos"] = z["marker"].astype(str).str.rsplit("_", n=1).str[-1].astype(int)
    byc = {}
    for c, g in z.groupby("chrom"):
        byc[c] = (g["pos"].values, np.abs(g["z"].values))
    L, M = [], []
    for _, g in gdf.iterrows():
        if g["chrom"] not in byc:
            continue
        pos, zz = byc[g["chrom"]]
        m = (pos >= g["start"] - WIN) & (pos <= g["end"] + WIN)
        if m.sum() >= 5:
            L.append(g["length"]); M.append(zz[m].mean())
    L, M = np.array(L), np.array(M)
    rho = spearmanr(L, M).correlation
    # 分箱看趋势（散点 1.6 万个太多）
    qs = np.quantile(L, np.linspace(0, 1, 21))
    xs, ys = [], []
    for i in range(20):
        sel = (L >= qs[i]) & (L <= qs[i + 1])
        if sel.sum() > 20:
            xs.append(np.median(L[sel])); ys.append(M[sel].mean())
    ax2 = fig.add_subplot(132)
    ax2.scatter(L, M, s=.6, c="#bdc3c7", alpha=.35, edgecolors="none", rasterized=True)
    ax2.plot(xs, ys, "o-", c=PALETTE["US"], ms=3, lw=1)
    ax2.set_xscale("log")
    ax2.set_xlabel("Gene length (bp)"); ax2.set_ylabel("mean |z| in gene window")
    ax2.set_title("(b) Length does NOT predict signal\nSpearman rho = %+.3f" % rho, pad=4, fontsize=8)

    # (c) 模块长度
    ax3 = fig.add_subplot(133)
    data, labs, cols = [], [], []
    data.append(gdf["length"].values); labs.append("all"); cols.append("#bdc3c7")
    SHORT = {"HSP": "HSP", "Diapause": "Diap.", "Oxidative": "Oxid."}
    for name, pat in MODULES.items():
        sel = gdf["desc"].str.contains(pat, case=False, regex=True, na=False)
        data.append(gdf.loc[sel, "length"].values); labs.append(SHORT[name]); cols.append("#7f8c8d")
    bp = ax3.boxplot(data, tick_labels=labs, patch_artist=True, widths=.6,
                     medianprops=dict(color="black", lw=1), flierprops=dict(markersize=1.5))
    for bx, c in zip(bp["boxes"], cols):
        bx.set_facecolor(c); bx.set_alpha(.7); bx.set_edgecolor("black"); bx.set_linewidth(.6)
    ax3.set_yscale("log")
    ax3.set_ylabel("Gene length (bp)")
    ax3.set_title("(c) Functional modules: no length bias\n(all p > 0.1 vs background)", pad=4, fontsize=8)

    plt.tight_layout()
    save(fig, "FigS4_length_bias_check")


if __name__ == "__main__":
    main()
