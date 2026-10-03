#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""扩展选样：每个采样地取 N 个个体（覆盖度优先），产出第二批下载清单。

与 pick_samples.py 的区别：
  - 不再设深度上限（已核查 >70x 的 24 个都是野外个体，无 pool-seq）
  - 改为用 exclude_runs.txt（细胞系 / 近交品系）控制
  - 每个采样地取 8 个（群体遗传学建议每群体 8-15 个体）
  - 自动排除已在第一批里的 run
"""
import csv, os, collections

MATRIX = r"C:\SF_data\tools\sfru_wgs_matrix.tsv"
EXCLUDE = r"C:\SF_data\tools\exclude_runs.txt"
BATCH1 = r"C:\SF_data\tools\batch1_picks.tsv"
OUT = r"C:\SF_data\tools\batch2_picks.tsv"

GENOME = 384_000_000
TARGET = 10
BYTES_PER_BASE = 0.40
PER_SITE = 8
DMIN = 12.0

excl = set()
if os.path.exists(EXCLUDE):
    excl = {l.strip() for l in open(EXCLUDE, encoding="utf-8") if l.strip()}

have = set()
if os.path.exists(BATCH1):
    with open(BATCH1, encoding="utf-8") as f:
        next(f, None)
        have = {row.split("\t")[0] for row in f if row.strip()}

rows = []
with open(MATRIX, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        try:
            d = float(r["depth_x"])
        except (ValueError, TypeError):
            continue
        if r["has_fastq"] != "Y" or d < DMIN:
            continue
        if r["run"] in excl or r["run"] in have:
            continue
        rows.append({**r, "depth": d})

by_site = collections.defaultdict(list)
for x in rows:
    by_site[x["country"] or "(未标)"].append(x)

picks = []
for site, g in by_site.items():
    g = sorted(g, key=lambda x: -x["depth"])[:PER_SITE]
    picks.extend(g)

unit = TARGET * GENOME * BYTES_PER_BASE / 1e9
print(f"合格样本池: {len(rows)}")
print(f"第一批已有: {len(have)}")
print(f"本次新增  : {len(picks)} 个（每地最多 {PER_SITE} 个，覆盖 {len(by_site)} 个采样地）")
print(f"下载量    : {len(picks)*unit:.1f} GB")
print(f"按 16 MB/s 需 {len(picks)*unit*1024/16/3600:.1f} 小时")

with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["run", "country", "region", "depth_x", "pct_to_download", "study"])
    for x in sorted(picks, key=lambda x: (x["region"], x["country"], -x["depth"])):
        pct = max(1, int(min(1.0, TARGET / x["depth"]) * 100))
        w.writerow([x["run"], x["country"], x["region"], round(x["depth"], 1), pct, x["study"]])
print(f"已写出: {OUT}")
