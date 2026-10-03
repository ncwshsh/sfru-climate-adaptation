#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""汇总 S. frugiperda 全部 ENA WGS run，按地理大区聚合，产出可用于选样的主清单。

输入: C:\SF_data\tools\sfru_wgs_master.tsv  (ENA portal search 导出)
输出: 打印分区汇总 + 写 sfru_wgs_matrix.tsv

覆盖深度 = base_count / 基因组大小(384 Mb)
"""
import csv, sys, collections, statistics, re

SRC = r"C:\SF_data\tools\sfru_wgs_master.tsv"
OUT = r"C:\SF_data\tools\sfru_wgs_matrix.tsv"
GENOME = 384_000_000

def region(country: str) -> str:
    c = (country or "").strip()
    if not c:
        return "未知"
    head = c.split(":")[0].strip()
    americas = {"USA", "United States", "Brazil", "Mexico", "Puerto Rico", "Canada",
                "Argentina", "Colombia", "Peru", "Guatemala", "Honduras", "Nicaragua",
                "Costa Rica", "Panama", "Jamaica", "Cuba", "Dominican Republic", "Trinidad and Tobago"}
    africa = {"Zambia", "Ghana", "Rwanda", "Malawi", "Sudan", "Kenya", "Senegal", "Benin",
              "Nigeria", "Tanzania", "Uganda", "Ethiopia", "Egypt", "South Africa", "Mozambique",
              "Cameroon", "Mali", "Burkina Faso", "Togo", "Madagascar", "Zimbabwe", "Congo", "Guinea"}
    asia = {"China", "India", "Japan", "Korea", "South Korea", "Thailand", "Vietnam", "Malaysia",
            "Indonesia", "Philippines", "Bangladesh", "Pakistan", "Myanmar", "Cambodia", "Laos",
            "Nepal", "Sri Lanka", "Taiwan", "Israel", "Turkey", "Saudi Arabia", "Yemen", "Iran"}
    europe = {"France", "Spain", "Italy", "Germany", "Netherlands", "United Kingdom", "Portugal",
              "Belgium", "Switzerland", "Poland", "Greece"}
    oceania = {"Australia", "New Zealand", "Papua New Guinea"}
    if head in americas: return "美洲(源区+扩散)"
    if head in africa:   return "非洲"
    if head in asia:     return "亚洲"
    if head in europe:   return "欧洲"
    if head in oceania:  return "大洋洲"
    return "其他/待判"

rows = []
with open(SRC, encoding="utf-8") as f:
    r = csv.DictReader(f, delimiter="\t")
    for row in r:
        try:
            bc = int(row.get("base_count") or 0)
        except ValueError:
            bc = 0
        rows.append({
            "run": row.get("run_accession", ""),
            "study": row.get("study_accession", ""),
            "sample": row.get("sample_accession", ""),
            "platform": row.get("instrument_platform", ""),
            "model": row.get("instrument_model", ""),
            "layout": row.get("library_layout", ""),
            "bases": bc,
            "country": (row.get("country") or "").strip(),
            "date": row.get("collection_date", ""),
            "has_fq": "Y" if (row.get("fastq_bytes") or "").strip() else "N",
        })

print(f"读入 {len(rows)} 条 WGS run\n")

# 按大区聚合
grp = collections.defaultdict(list)
for x in rows:
    grp[region(x["country"])].append(x)

print(f"{'大区':<16}{'run数':>6}{'有fastq':>8}{'中位数深度':>10}{'碱基(Tb)':>10}")
print("-" * 52)
for reg in sorted(grp, key=lambda k: -len(grp[k])):
    g = grp[reg]
    depths = [x["bases"] / GENOME for x in g if x["bases"] > 0]
    med = statistics.median(depths) if depths else 0
    nfq = sum(1 for x in g if x["has_fq"] == "Y")
    tb = sum(x["bases"] for x in g) / 1e12
    print(f"{reg:<16}{len(g):>6}{nfq:>8}{med:>10.1f}x{tb:>10.2f}")

print("\n=== 各国/地区明细（run 数 >= 5）===")
cg = collections.defaultdict(list)
for x in rows:
    cg[x["country"] or "(空)"].append(x)
print(f"{'country':<48}{'run数':>6}{'中位深度':>9}{'有fq':>6}")
print("-" * 70)
for c in sorted(cg, key=lambda k: -len(cg[k])):
    g = cg[c]
    if len(g) < 5:
        continue
    depths = [x["bases"] / GENOME for x in g if x["bases"] > 0]
    med = statistics.median(depths) if depths else 0
    nfq = sum(1 for x in g if x["has_fq"] == "Y")
    print(f"{c[:46]:<48}{len(g):>6}{med:>9.1f}x{nfq:>6}")

# 写出带大区标注的主清单
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["run", "study", "sample", "region", "country", "date",
                "platform", "model", "layout", "bases", "depth_x", "has_fastq"])
    for x in rows:
        w.writerow([x["run"], x["study"], x["sample"], region(x["country"]), x["country"],
                    x["date"], x["platform"], x["model"], x["layout"], x["bases"],
                    round(x["bases"] / GENOME, 2), x["has_fq"]])
print(f"\n已写出: {OUT}")
