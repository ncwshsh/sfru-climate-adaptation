#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""基于覆盖深度与地理分布，给出降覆盖下载（统一降到 10x）的选样建议。

核心逻辑：
  目标 10x -> 需 3.84 Gb 碱基 -> 按实测压缩比 0.4 B/碱基 ≈ 1.5 GB 下载量/样本
  原始深度 >= 10x 的 run 才能"安全"降到 10x；不足 10x 的必须全量下且仍不达标
"""
import csv, collections, statistics

PATH = r"C:\SF_data\tools\sfru_wgs_matrix.tsv"
GENOME = 384_000_000
TARGET_DEPTH = 10          # 目标覆盖
BYTES_PER_BASE = 0.40      # 实测压缩比

rows = []
with open(PATH, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        try:
            d = float(r["depth_x"])
            b = int(r["bases"])
        except (ValueError, TypeError):
            continue
        rows.append({**r, "depth": d, "bases": b})

print(f"总样本 {len(rows)}\n")

# ---- 深度分档 ----
bins = [("<5x", 0, 5), ("5-10x", 5, 10), ("10-15x", 10, 15),
        ("15-30x", 15, 30), ("30-60x", 30, 60), (">=60x", 60, 1e9)]
print("=== 深度分档 ===")
print(f"{'档位':<10}{'样本数':>8}{'占比':>8}")
for name, lo, hi in bins:
    n = sum(1 for x in rows if lo <= x["depth"] < hi)
    print(f"{name:<10}{n:>8}{n/len(rows)*100:>7.1f}%")

# 深度窗口：够用且不太可能是 pool-seq / 特殊实验设计
# 上限 70x：>=100x 的样本往往是混池测序(pool-seq)或单个体超深测序，
#           混池不能当个体参与群体遗传学分析 -> 单独核实前一律排除
DMIN, DMAX = 12.0, 70.0
elig = [x for x in rows
        if DMIN <= x["depth"] <= DMAX and x["has_fastq"] == "Y"]
skipped = sum(1 for x in rows if x["depth"] > DMAX)
print(f"\n筛选条件: {DMIN}~{DMAX}x 且可得 FASTQ -> {len(elig)} 个合格样本")
print(f"（{skipped} 个 >{DMAX}x 的超深样本已排除，疑似 pool-seq，需单独核实）")

# ---- 按地区统计合格样本 ----
print("\n=== 合格样本（>=10x）按地区分布 ===")
reg = collections.defaultdict(list)
for x in elig:
    reg[x["country"] or "(未标国别)"].append(x)
print(f"{'country':<42}{'n':>5}{'中位深度':>9}{'代表性采样地」':>4}")
for c in sorted(reg, key=lambda k: -len(reg[k])):
    g = reg[c]
    if len(g) < 3:
        continue
    med = statistics.median([x["depth"] for x in g])
    print(f"{c[:40]:<42}{len(g):>5}{med:>9.1f}x")

# ---- 每个样本降到 10x 的下载量 ----
for x in elig:
    frac = TARGET_DEPTH / x["depth"]
    x["dl_gb"] = 3.84e9 * BYTES_PER_BASE / 1e9   # 恒为 ~1.54GB（降到 10x）
    x["frac"] = min(frac, 1.0)

print(f"\n=== 下载预算（每个样本统一降到 {TARGET_DEPTH}x）===")
unit = 3.84e9 * BYTES_PER_BASE / 1e9
print(f"  单样本下载量约 {unit:.2f} GB")
for n in (20, 30, 50, 100, 200):
    tot = n * unit
    print(f"  {n:>4} 个样本 -> {tot:>6.1f} GB   "
          f"(3.1MB/s 需 {tot*1024/3.1/3600:>5.1f} h | 0.15MB/s 需 {tot*1024/0.15/3600:>6.1f} h)")

# ---- 输出推荐清单：每地取若干深度最高的 ----
print("\n=== 推荐首批（各地取深度最高的前 N 个）===")
PER_SITE = 3
picks = []
for c, g in reg.items():
    if len(g) < 3:
        continue
    g2 = sorted(g, key=lambda x: -x["depth"])[:PER_SITE]
    picks.extend(g2)
seen = set()
uniq = []
for x in picks:
    if x["run"] in seen:
        continue
    seen.add(x["run"])
    uniq.append(x)
tot_gb = len(uniq) * unit
print(f"  汇总: {len(uniq)} 个样本，覆盖 {len(reg)} 个采样地，约 {tot_gb:.1f} GB")
print(f"  按 3.1 MB/s 估算需 {tot_gb*1024/3.1/3600:.1f} 小时")

with open(r"C:\SF_data\tools\batch1_picks.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["run", "country", "region", "depth_x", "pct_to_download", "study"])
    for x in sorted(uniq, key=lambda x: (x["region"], x["country"])):
        pct = int(x["frac"] * 100)
        if pct < 1:
            pct = 1
        w.writerow([x["run"], x["country"], x["region"], round(x["depth"], 1), pct, x["study"]])
print("  已写出: C:\\SF_data\\tools\\batch1_picks.tsv (pct_to_download = 只下前百分之几)")
