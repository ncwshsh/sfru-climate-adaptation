# -*- coding: utf-8 -*-
"""按 12~15x + ANGSD 标准重算合格池与下载计划。

规则（胡博士 2026-09-17 决定）：
  门槛   : 真实深度 >= 20x  （可达 usable >= 12x）
  下载目标: 名义 min(真实深度, 25x)  -> 能到 15x 就下到 15x，否则下满（>=12x）
  平台   : 仅短读长（剔除 PacBio / Nanopore）
  类型   : 仅 FIELD（野外种群）
成本：换比例必须整份重下 -> 每样本 GB = GPX x 目标名义深度，GPX = 5.65/25 = 0.226
"""
import csv, os, collections, statistics

T = r"C:\SF_data\tools"
GPX = 5.65 / 25.0
FLOOR_D = 20.0      # 门槛：真实深度（可用 12x）
CAP_D = 25.0        # 目标上限：名义 25x（可用 15x）
BW = 2.4            # MB/s

rows = list(csv.DictReader(open(os.path.join(T, "cohort_candidates.tsv"),
                                encoding="utf-8"), delimiter="\t"))
field = [r for r in rows if r["type"] == "FIELD"]

qual = []
for r in field:
    d = float(r["depth_true_x"] or 0)
    if d < FLOOR_D:
        continue
    tgt_nom = min(d, CAP_D)
    gb = GPX * tgt_nom
    r["_d"] = d
    r["_tgt_nom"] = tgt_nom
    r["_usable"] = tgt_nom * 0.6
    r["_gb"] = gb
    qual.append(r)

out = os.path.join(T, "cohort_pool_1215x.tsv")
cols = ["run", "study", "region", "country", "date", "platform", "layout",
        "depth_true_x", "_tgt_nom", "_usable", "_gb", "pct_needed_full",
        "need_coord", "need_strain", "latlon", "host"]
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(cols)
    for r in sorted(qual, key=lambda x: (x["region"], x["country"], -x["_d"])):
        r["pct_needed_full"] = f"{min(100.0, 25.0/r['_d']*100):.1f}"
        w.writerow([r.get(c, "") for c in cols])

print(f"野外种群 {len(field)} -> 合格（真实深度>=20x）{len(qual)}")
tot = sum(r["_gb"] for r in qual)
print(f"全部下完：{tot:.1f} GB ({tot/1000:.2f} TB)  ≈ {tot*1024/BW/3600:.0f} h ≈ {tot*1024/BW/3600/24:.1f} 天\n")

print("=== 按区域/国家 ===")
rc = collections.Counter((r["region"], (r["country"] or "?").split(":")[0].strip())
                         for r in qual)
for (reg, ct), v in sorted(rc.items()):
    sub = [r for r in qual if r["region"] == reg and (r["country"] or "").split(":")[0].strip() == ct]
    print(f"  {reg:<20}{ct:<16}{v:>3}  深 {min(x['_d'] for x in sub):.0f}~{max(x['_d'] for x in sub):.0f}x"
          f"  {sum(x['_gb'] for x in sub):>6.1f} GB")

print("\n=== 按平台 ===")
for k, v in collections.Counter(r["platform"] for r in qual).most_common():
    print(f"  {k:<16}{v:>3}  {sum(x['_gb'] for x in qual if x['platform']==k):>6.1f} GB")

print("\n=== 目标深度分布 ===")
us = [r["_usable"] for r in qual]
print(f"  usable 目标: 中位 {statistics.median(us):.1f}x  区间 {min(us):.1f}~{max(us):.1f}x")
print(f"  单样本下载: 中位 {statistics.median([r['_gb'] for r in qual]):.2f} GB")

print("\n=== 与 20x 标准对比 ===")
q20 = [r for r in field if r["_d"] >= 33.33]
print(f"  20x 标准: {len(q20)} 样本 / {sum(r['_d']*GPX*min(1,33.33/r['_d']) for r in q20):.0f} GB")
print(f"  12~15x : {len(qual)} 样本 / {tot:.0f} GB")
print(f"  => 同样预算下多出 {len(qual)-len(q20)} 个样本")
print(f"\n[写出] {out}")
