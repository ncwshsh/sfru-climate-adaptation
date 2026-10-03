# -*- coding: utf-8 -*-
"""PRJNA1115088（佛罗里达/美国大规模低深度队列）的空间覆盖与深度画像。

动机：项目设计核心是「源区（美洲佛罗里达）→ 非洲 → 中国」，但合格池（深度>=20x）里没有佛罗里达。
      而 PRJNA1115088 有 391 个 USA 样本、**县级坐标**，深度却只有 ~5~7x。
      ⇒ 存在「深度 vs 空间覆盖」的定量权衡，需要看清规模。
"""
import csv, collections, statistics, os

M = r"C:\SF_data\tools\sfru_wgs_matrix.tsv"
rows = list(csv.DictReader(open(M, encoding="utf-8"), delimiter="\t"))

for st in ["PRJNA1115088", "PRJNA639296"]:
    v = [r for r in rows if r["study"] == st]
    if not v:
        continue
    print("=" * 96)
    print(f"{st}  n={len(v)}")
    print("=" * 96)
    d = [float(r["depth_x"] or 0) for r in v]
    print(f"  深度: 中位 {statistics.median(d):.1f}x  [{min(d):.1f} ~ {max(d):.1f}]")
    bins = [(0,3),(3,6),(6,10),(10,20),(20,34),(34,1000)]
    for lo, hi in bins:
        n = sum(1 for x in d if lo <= x < hi)
        print(f"    {lo:>3}-{hi:<5}x  n={n:<4}{'#'*int(n/8)}")

    print(f"\n  --- 国家/行政区 ---")
    ct = collections.Counter((r.get("country") or "?").split(":")[0].strip() for r in v)
    for k, c in ct.most_common(12):
        print(f"    {k:<24}{c}")

    print(f"\n  --- 次级地名（州/县）前 20 ---")
    sub = collections.Counter((r.get("country") or "").split(":", 1)[1].strip()
                              if ":" in (r.get("country") or "") else "(无)" for r in v)
    for k, c in sub.most_common(20):
        print(f"    {k:<44}{c}")
    print(f"    次级地名唯一值总数 = {len(sub)}")

    print(f"\n  --- 日期 ---")
    dt = collections.Counter((r.get("date") or "?")[:7] for r in v)
    for k, c in dt.most_common(8):
        print(f"    {k:<12}{c}")
    print()

# 全库里有「县级 / County」分辨率的样本
print("=" * 96)
print("全库中含 'County' 的样本（即县级分辨率）")
print("=" * 96)
cnty = [r for r in rows if "county" in (r.get("country") or "").lower()]
print(f"  总数 = {len(cnty)}")
for k, c in collections.Counter(r["study"] for r in cnty).most_common():
    dd = [float(r["depth_x"] or 0) for r in cnty if r["study"] == k]
    print(f"    {k:<16}{c:>4}  深度中位 {statistics.median(dd):.1f}x")
for k, c in collections.Counter((r.get("country") or "").split(":")[0].strip()
                                for r in cnty).most_common(10):
    print(f"    {k:<24}{c}")

# 全库分国：有几次级地名 + 深度分布
print("\n" + "=" * 96)
print("全库分国：样本数 / 有次级地名比例 / 深度中位")
print("=" * 96)
byc = collections.defaultdict(list)
for r in rows:
    byc[(r.get("country") or "?").split(":")[0].strip()].append(r)
for ct, v in sorted(byc.items(), key=lambda x: -len(x[1]))[:16]:
    withsub = sum(1 for r in v if ":" in (r.get("country") or ""))
    d = [float(r["depth_x"] or 0) for r in v]
    print(f"  {ct:<24}{len(v):>5} 样本  {withsub:>5} 有次级地名({withsub/len(v)*100:>3.0f}%)  "
          f"深度中位 {statistics.median(d):>6.1f}x")
