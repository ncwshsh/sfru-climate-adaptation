# -*- coding: utf-8 -*-
"""extract_strain_region.py —— 从已有 beagle 里提取株系标记区（Tpi / Flightin）的基因型

⚠️ 踩坑记录：ANGSD 的 marker 名是 `NC_064236.1_8180000` 这种**三段式**
   （染色体名本身含下划线！）。按 "_" 取第 2 段会拿到 "064236.1" 而不是位置。
   必须用 rsplit("_", 1) 或取最后一段。
"""
import os
import gzip
import numpy as np

BEAGLE = "/home/hugo/data/angsd/beagle_1M.beagle.gz"
OUT = "/home/hugo/data/angsd/strain_region_geno.tsv"
CHR = "NC_064236.1"
REGIONS = [(8180000, 8200000, "Tpi"), (6860000, 6880000, "Flightin")]


def main():
    rows = []
    with gzip.open(BEAGLE, "rt") as fh:
        header = fh.readline().split()
        for line in fh:
            p = line.split()
            mk = p[0]
            if not mk.startswith(CHR + "_"):
                continue
            pos = int(mk.rsplit("_", 1)[1])
            tag = None
            for lo, hi, nm in REGIONS:
                if lo <= pos <= hi:
                    tag = nm
                    break
            if tag is None:
                continue
            vals = np.array(p[3:], dtype=np.float32)
            dose = vals[1::3] + 2.0 * vals[2::3]        # 期望剂量 0~2
            rows.append((mk, pos, tag, dose))
    print("提取到 %d 个位点" % len(rows))
    from collections import Counter
    c = Counter(r[2] for r in rows)
    print("  %s" % dict(c))

    # 写表：行 = 位点，列 = marker, pos, region, 然后 214 个个体的剂量
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("marker\tpos\tregion\t" + "\t".join("Ind%d" % i for i in range(len(rows[0][3]))) + "\n")
        for mk, pos, tag, dose in rows:
            fh.write("%s\t%d\t%s\t" % (mk, pos, tag) + "\t".join("%.3f" % v for v in dose) + "\n")
    print("已写出: %s" % OUT)


if __name__ == "__main__":
    main()
