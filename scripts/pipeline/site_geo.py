# -*- coding: utf-8 -*-
"""把 243 个野外样本的地理字符串整理成「可地理编码」的分辨率分层表。

发现（2026-09-17）：
  ENA 的 country 字段分辨率**差异极大**，但比预想好很多：
    - 巴西 33 个 → **市级**（municipality + state），可精确地理编码
    - 马来西亚 32 个 → 州级
    - 中国 32 个 → 省级（12 个只到国家）
    - 塞内加尔 51 个 → 区域级（Casamance）
    - 其余 74 个 → 仅国家级
  ⇒ 气候梯度**不必等论文级人工整理就能先跑**，用行政质心即可起步。
输出 site_geo.tsv：地理字符串 / 样本数 / 分辨率等级 / 所属国家 / 纬度跨度评估
"""
import csv, os, collections, re

T = r"C:\SF_data\tools"
rows = [r for r in csv.DictReader(
    open(os.path.join(T, "cohort_candidates.tsv"), encoding="utf-8"), delimiter="\t")
    if r["type"] == "FIELD"]


def resolution(s):
    s = s.strip()
    core = s.split(":", 1)[1].strip() if ":" in s else ""
    if not core:
        return "仅国家级", 0
    # 巴西 "Municipio, Estado"
    if "," in core:
        return "市级(municipality+state)", 3
    # 有省/州形态词
    if re.search(r"(Province|State|Negeri|Selangor|Malacca|Guangdong|Yunnan|Zhejiang)", core, re.I):
        return "州/省级", 2
    if re.search(r"^(Casamance)$", core, re.I):
        return "区域级", 2
    return "次级(未分类)", 1


cnt = collections.Counter(r["country"].strip() for r in rows)
out = []
for s, n in cnt.most_common():
    res, lvl = resolution(s)
    country = s.split(":")[0].strip() if ":" in s else s.strip()
    out.append((s, country, n, res, lvl))

with open(os.path.join(T, "site_geo.tsv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["geo_string", "country", "n_samples", "resolution", "level",
                "lat", "lon", "source_note"])
    for s, c, n, res, lvl in out:
        w.writerow([s, c, n, res, lvl, "", "", ""])

print(f"{'地理字符串':<42}{'样本':>5}  {'分辨率'}")
print("-" * 74)
for s, c, n, res, lvl in sorted(out, key=lambda x: (-x[4], -x[2])):
    print(f"{s:<42}{n:>5}  {res}")

print("\n=== 分辨率汇总 ===")
agg = collections.Counter()
for s, c, n, res, lvl in out:
    agg[res] += n
for k, v in agg.most_common():
    print(f"  {k:<28}{v:>4} 样本  ({v/len(rows)*100:.0f}%)")

print("\n=== 可做「国内梯度」的国家 ===")
for c in ["Brazil", "Malaysia", "China", "Senegal"]:
    sub = [x for x in out if x[1] == c]
    tot = sum(x[2] for x in sub)
    lv = max((x[4] for x in sub), default=0)
    print(f"  {c:<12}{tot:>4} 样本  最高分辨率等级 {lv}  ({max((x[3] for x in sub), default='-')})")

print(f"\n[写出] {os.path.join(T, 'site_geo.tsv')}")
