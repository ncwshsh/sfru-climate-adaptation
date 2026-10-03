# -*- coding: utf-8 -*-
"""为 S2 正式队列（cohort_v3.tsv）重建地理表。

旧 site_geo.tsv 只覆盖 243 野外池，不含 S2 新增的 PRJNA1115088（美国 14 县）。
本脚本按 S2 的 run 集重建，并给出 Nominatim 查询串。
"""
import csv, os, collections, re

T = r"C:\SF_data\tools"
M = os.path.join(T, "sfru_wgs_matrix.tsv")
CO = os.path.join(T, "cohort_v3.tsv")

runs = {}
for r in csv.DictReader(open(CO, encoding="utf-8"), delimiter="\t"):
    runs[r["run"]] = r["module"]

rows = [r for r in csv.DictReader(open(M, encoding="utf-8"), delimiter="\t")
        if r["run"] in runs]

# 分模块保留，便于判断"哪个模块贡献多少空间点"
per_mod = collections.defaultdict(collections.Counter)
for r in rows:
    c = (r.get("country") or "?").strip()
    c = re.sub(r"\s+", " ", c).rstrip(",")
    per_mod[runs[r["run"]]][c] += 1

print("模块 × 空间点")
print("-" * 90)
tot_pts = 0
for m in sorted(per_mod):
    print(f"\n【{m}】 {len(per_mod[m])} 个空间点 / {sum(per_mod[m].values())} 样本")
    for g, n in per_mod[m].most_common():
        print(f"    {n:>4}  {g}")
    tot_pts += len(per_mod[m])
print(f"\n空间点总计 {tot_pts}")

# ---- 写地理表 + 生成查询串 ----
def resolve(g):
    """返回 (resolution_level, nominatim_query)"""
    if ":" in g:
        ct, sb = [x.strip() for x in g.split(":", 1)]
    else:
        ct, sb = g, ""
    if not sb:
        return 0, ct, ct
    # 市级：'Palm Beach County, Florida' / 'Balsas, Maranhao'
    q = f"{sb}, {ct}"
    if "County" in sb or "Province" in sb:
        return 2, ct, q
    if "," in sb:
        return 3, ct, q
    return 2, ct, q


out = os.path.join(T, "site_geo_s2.tsv")
seen = []
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["geo_string", "country", "subnational", "n_samples", "module",
                "level", "lat", "lon", "source_note"])
    for m in sorted(per_mod):
        for g, n in sorted(per_mod[m].items(), key=lambda x: (-x[1], x[0])):
            lv, ct, q = resolve(g)
            w.writerow([g, ct, g.split(":", 1)[1].strip() if ":" in g else "",
                        n, m, lv, "", "", q])
            seen.append((g, ct, q, m, n))
print(f"\n[写出] {out}  {len(seen)} 行")
