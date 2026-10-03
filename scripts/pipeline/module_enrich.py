# -*- coding: utf-8 -*-
"""module_enrich.py —— 功能模块富集检验

"66 个候选里命中了 1 个 HSP" 说服力不够——因为它取决于阈值怎么切。
更有力的问法是：**HSP 基因附近的位点，其 RDA 载荷整体是否显著高于全基因组背景？**
（模块水平富集，而不是"数有几个"）

做法：
  1. 从 GFF 找出各功能模块的所有基因（按关键词）
  2. 取这些基因 ±20 kb 内的所有 SNP（在 20 万位点集里）
  3. 比较这些 SNP 的 |z(RDA1)| 与全基因组背景的 |z|
  4. 检验：Mann-Whitney U + 置换检验（随机抽同样个数的 SNP，重复 2000 次）
"""
import os
import re
import sys
import gzip
import numpy as np
import pandas as pd

ROOT = "/mnt/c/SF_data"
GFF = os.path.join(ROOT, "00_ref", "GCF_023101765.2_genomic.gff.gz")
ZFILE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tools", "report", "gea_rda_z.tsv")
WIN = 20000
NPERM = 2000
SEED = 7

MODULES = {
    "HSP/热激蛋白": r"heat shock|dnaJ|hsp\d|hsc70|chaperon",
    "滞育/光周期": r"diapause|circadian|clock|timeless|cryptochrome|juvenile hormone|"
                  r"ecdysone|vitellogenin",
    "氧化应激": r"catalase|peroxidase|superoxide|glutathione|peroxiredoxin|thioredoxin|"
               r"cytochrome p450",
}


def load_genes():
    genes = {}
    with gzip.open(GFF, "rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 9 or p[2] != "gene":
                continue
            d = re.search(r"description=([^;]+)", p[8])
            desc = (d.group(1) if d else "").replace("%2C", ",")
            m = re.search(r"Name=([^;]+)", p[8])
            genes.setdefault(p[0], []).append((int(p[3]), int(p[4]),
                                               m.group(1) if m else "", desc))
    return genes


def main():
    genes = load_genes()
    z = pd.read_csv(ZFILE, sep="\t")
    z["chrom"] = z["marker"].astype(str).str.rsplit("_", n=1).str[0]
    z["pos"] = z["marker"].astype(str).str.rsplit("_", n=1).str[-1].astype(int)
    az = np.abs(z["z"].values)
    print("位点 %d 个，|z| 背景均值 %.3f" % (len(az), az.mean()))

    # 建索引：按染色体排序的位点
    byc = {}
    for c, sub in z.groupby("chrom"):
        byc[c] = (sub["pos"].values, sub.index.values)

    rng = np.random.default_rng(SEED)
    print()
    print("%-14s %8s %8s %10s %10s %8s" % ("功能模块", "基因数", "位点数", "模块|z|均值", "背景均值", "置换p"))
    for name, pat in MODULES.items():
        idx = []
        ngene = 0
        for c, gl in genes.items():
            if c not in byc:
                continue
            pos_arr, idx_arr = byc[c]
            for (s, e, gname, desc) in gl:
                if not re.search(pat, desc, re.I):
                    continue
                ngene += 1
                lo, hi = s - WIN, e + WIN
                sel = (pos_arr >= lo) & (pos_arr <= hi)
                idx.extend(idx_arr[sel].tolist())
        idx = np.array(sorted(set(idx)))
        if len(idx) < 5:
            print("%-14s %8d %8d   （位点数不足，跳过）" % (name, ngene, len(idx)))
            continue
        obs = az[idx].mean()
        # 置换：随机抽同样多个位点
        cnt = 0
        for _ in range(NPERM):
            r = rng.choice(len(az), size=len(idx), replace=False)
            if az[r].mean() >= obs:
                cnt += 1
        p = (cnt + 1) / (NPERM + 1)
        print("%-14s %8d %8d %10.3f %10.3f %8.4f" % (name, ngene, len(idx), obs, az.mean(), p))


if __name__ == "__main__":
    main()
