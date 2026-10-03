# -*- coding: utf-8 -*-
"""module_length_check.py —— 模块富集是否也被"基因长度偏差"污染？

背景：GO 富集已被证明是基因长度偏差的产物（候选基因中位长度 2.42×背景）。
      那么主打结论（HSP / 氧化应激模块富集）会不会同样中招？
      两种可能的中招方式：
        A. 这些模块的基因本身更长 ⇒ 模块内的位点更多，但富集用的是**均值** |z|，
           均值对位点数量不敏感 ⇒ 若仅此一条，结论仍稳
        B. 长基因的 |z| 系统性偏高（承载更多变异/更多真信号）⇒ 模块若偏长，
           其 |z| 均值会被抬高 ⇒ 结论有偏
      所以必须**同时检验两件事**：模块基因的长度分布 + 长度与 |z| 的关系。
"""
import os
import re
import gzip
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr

ROOT = "/mnt/c/SF_data"
REP = os.path.join(ROOT, "tools", "report")
GFF = os.path.join(ROOT, "00_ref", "GCF_023101765.2_genomic.gff.gz")
WIN = 20000

MODULES = {
    "HSP": r"heat shock|dnaJ|hsp\d|hsc70|chaperon",
    "滞育": r"diapause|circadian|clock|timeless|cryptochrome|juvenile hormone|ecdysone|vitellogenin",
    "氧化应激": r"catalase|peroxidase|superoxide|glutathione|peroxiredoxin|thioredoxin|cytochrome p450",
}


def main():
    # 基因（位置 + 长度 + 描述）
    genes = []
    with gzip.open(GFF, "rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 9 or p[2] != "gene":
                continue
            d = re.search(r"description=([^;]+)", p[8])
            genes.append(dict(chrom=p[0], start=int(p[3]), end=int(p[4]),
                              length=int(p[4]) - int(p[3]) + 1,
                              desc=(d.group(1) if d else "").replace("%2C", ",")))
    gdf = pd.DataFrame(genes)
    print("基因数 %d，长度中位 %.0f bp" % (len(gdf), gdf["length"].median()))

    # 位点 z（用美国全量结果）
    z = pd.read_csv(os.path.join(REP, "gea_rda_z_full.tsv"), sep="\t")
    z["chrom"] = z["marker"].astype(str).str.rsplit("_", n=1).str[0]
    z["pos"] = z["marker"].astype(str).str.rsplit("_", n=1).str[-1].astype(int)
    az = np.abs(z["z"].values)
    print("位点 %d，|z| 背景均值 %.3f" % (len(az), az.mean()))

    # 每个基因取窗口内位点的 |z| 均值
    byc = {}
    for c, g in z.groupby("chrom"):
        byc[c] = (g["pos"].values, np.abs(g["z"].values))
    gl_means, gl_lens = [], []
    for _, g in gdf.iterrows():
        if g["chrom"] not in byc:
            continue
        pos, zz = byc[g["chrom"]]
        m = (pos >= g["start"] - WIN) & (pos <= g["end"] + WIN)
        if m.sum() >= 5:
            gl_means.append(zz[m].mean())
            gl_lens.append(g["length"])
    gl_means = np.array(gl_means); gl_lens = np.array(gl_lens)
    print("可用于分析的基因 %d" % len(gl_means))

    # ---- 检验 B：长度与 |z| 的关系 ----
    print()
    print("=== 检验 B：基因长度 vs 该基因窗口内 |z| 均值 ===")
    rho = spearmanr(gl_lens, gl_means).correlation
    print("  Spearman rho = %+.3f" % rho)
    q = np.quantile(gl_lens, [0.25, 0.5, 0.75])
    for lab, sel in [("最短 25%%", gl_lens <= q[0]), ("中位附近", (gl_lens > q[0]) & (gl_lens <= q[2])),
                     ("最长 25%%", gl_lens > q[2])]:
        print("  %-10s n=%-5d  长度中位 %7.0f   |z|均值 %.4f"
              % (lab, sel.sum(), np.median(gl_lens[sel]), gl_means[sel].mean()))
    print("  （若最长 25%% 的 |z| 明显高于最短 25%%，则长度确实与信号强度正相关）")

    # ---- 检验 A：模块基因的长度分布 ----
    print()
    print("=== 检验 A：各功能模块基因的长度 vs 其余基因 ===")
    all_len = gl_lens
    for name, pat in MODULES.items():
        sel = gdf["desc"].str.contains(pat, case=False, regex=True, na=False)
        L = gdf.loc[sel, "length"].values
        u, p = mannwhitneyu(L, gdf.loc[~sel, "length"].values, alternative="two-sided")
        print("  %-8s n=%-4d 长度中位 %7.0f  其余 %7.0f  比 %.2fx  Mann-Whitney p=%.3g"
              % (name, len(L), np.median(L), gdf.loc[~sel, "length"].median(),
                 np.median(L) / gdf.loc[~sel, "length"].median(), p))

    print()
    print("判读：")
    print("  - 若各模块长度与其他基因无显著差异 ⇒ 模块富集结论不受长度偏差影响")
    print("  - 若某模块显著更长 **且** 长度与 |z| 正相关 ⇒ 该模块的富集需谨慎，")
    print("    应做长度匹配的模块富集作为敏感性分析")


if __name__ == "__main__":
    main()
