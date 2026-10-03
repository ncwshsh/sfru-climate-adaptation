# -*- coding: utf-8 -*-
"""annotate_candidates.py —— 把 RDA 找出的气候关联候选位点映射到基因，
                            并重点检查是否落在三个功能模块（HSP / 滞育 / 氧化应激）

项目目标就是这三个模块：
  1. 热激蛋白 HSP —— 温度适应
  2. 滞育 / 光周期响应 —— 越冬与季节性
  3. 氧化应激 —— 逆境耐受

做法：解析 NCBI GFF（GCF_023101765.2），建 31 条染色体的基因区间索引，
      对每个候选位点找窗口内（默认 ±20 kb）的基因，并按关键词打标签。
"""
import os
import re
import sys
import gzip
import pandas as pd

ROOT = "/mnt/c/SF_data"
GFF = os.path.join(ROOT, "00_ref", "GCF_023101765.2_genomic.gff.gz")
CAND = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tools", "report", "gea_candidates.tsv")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "tools", "report", "gea_candidates_annotated.tsv")
WIN = 20000   # 位点上下游窗口（bp）

# 功能模块关键词
MODULES = {
    "HSP/热激蛋白": r"heat shock|hsp|chaperon|dnaJ|hsc70|grp78|grp94|alpha-crystallin|small heat",
    "滞育/光周期": r"diapause|circadian|clock|period|timeless|cryptochrome|photoperiod|"
                  r"juvenile hormone|ecdysone|vitellogenin|dormancy|cry\b|per\b|clockwork",
    "氧化应激": r"oxidative|catalase|peroxidase|superoxide|glutathione|peroxiredoxin|"
               r"thioredoxin|cytochrome p450|cyp4|cyp6|cyp9|antioxidant",
    "解毒/代谢": r"glutathione s-transferase|gst|carboxylesterase|esterase|acetylcholinesterase|"
                r"udp-glucuronosyl|transferase",
    "离子/渗透": r"aquaporin|sodium|potassium|calcium channel|ion channel|osmo|trehalose",
}


def main():
    # ---- 解析 GFF：只要 gene 行 ----
    genes = {}
    with gzip.open(GFF, "rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 9 or p[2] != "gene":
                continue
            chrom, start, end = p[0], int(p[3]), int(p[4])
            attr = p[8]
            m = re.search(r"Name=([^;]+)", attr)
            name = m.group(1) if m else ""
            d = re.search(r"description=([^;]+)", attr)
            desc = d.group(1) if d else ""
            desc = desc.replace("%2C", ",").replace("%3B", ";")
            genes.setdefault(chrom, []).append((start, end, name, desc))
    for c in genes:
        genes[c].sort()
    print("已载入 %d 条染色体、%d 个基因" % (len(genes), sum(len(v) for v in genes.values())))

    # ---- 读候选位点 ----
    cand = pd.read_csv(CAND, sep="\t")
    print("候选位点 %d 个" % len(cand))

    rows = []
    for _, r in cand.iterrows():
        chrom, pos = str(r["chrom"]), int(r["pos"])
        hits = []
        if chrom in genes:
            for (s, e, name, desc) in genes[chrom]:
                if s - WIN <= pos <= e + WIN:
                    hits.append((abs(pos - (s + e) / 2.0), name, desc, s, e))
        hits.sort()
        if hits:
            near = hits[0]
            rows.append(dict(marker=r["marker"], chrom=chrom, pos=pos,
                             loading=r.get("RDA1_loading", ""), z=r["z"],
                             maf=r.get("maf_est", ""),
                             gene=near[1], desc=near[2][:120],
                             dist=int(near[0]), gstart=near[3], gend=near[4]))
        else:
            rows.append(dict(marker=r["marker"], chrom=chrom, pos=pos,
                             loading=r.get("RDA1_loading", ""), z=r["z"],
                             maf=r.get("maf_est", ""),
                             gene="(基因间区)", desc="", dist=-1, gstart="", gend=""))

    out = pd.DataFrame(rows)

    # 打功能模块标签
    def tag(desc):
        t = []
        for k, pat in MODULES.items():
            if re.search(pat, desc, re.I):
                t.append(k)
        return ";".join(t)
    out["module_hit"] = out["desc"].map(tag)
    out.to_csv(OUT, sep="\t", index=False)
    print("已写出: %s" % OUT)

    # ---- 汇总 ----
    print()
    print("=== 候选位点落在哪个功能模块 ===")
    for k in MODULES:
        sub = out[out["module_hit"].str.contains(k, na=False)]
        print("  %-14s %d 个" % (k, len(sub)))
        for _, rr in sub.head(6).iterrows():
            print("      %-24s %-16s %s" % (rr["gene"], "%s:%d" % (rr["chrom"][-6:], rr["pos"]),
                                            rr["desc"][:56]))
    print()
    print("=== 落在基因间区的候选位点: %d 个 ===" % (out["gene"] == "(基因间区)").sum())
    print()
    print("=== 所有有基因注释的候选（按 |z| 降序，前 15）===")
    for _, rr in out[out["gene"] != "(基因间区)"].sort_values(
            "z", key=lambda s: s.abs(), ascending=False).head(15).iterrows():
        print("  %-22s z=%+6.2f  %-16s %s" % (rr["gene"], rr["z"],
                                              "%s:%d" % (rr["chrom"][-6:], rr["pos"]),
                                              rr["desc"][:60]))


if __name__ == "__main__":
    main()
