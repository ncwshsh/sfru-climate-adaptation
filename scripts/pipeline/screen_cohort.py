# -*- coding: utf-8 -*-
"""队列筛选：从 deep_pool_20x.tsv（286 个 usable>=20x 候选）中筛出技术可比、区域可平
衡的正式队列候选。

筛选维度：
  1) 测序平台/文库类型  —— 短读长必须（剔除 PACBIO_SMRT / OXFORD_NANOPORE）
  2) library_layout     —— 优先 PAIRED
  3) 区域/国家分布      —— 看气候梯度是否可做（是否有足够空间跨度）
  4) 经纬度覆盖         —— 有坐标的优先（气候变量提取要用）
输出：screen_cohort_out.tsv + 控制台报告
"""
import csv, os, collections

T = r"C:\SF_data\tools"
POOL = os.path.join(T, "deep_pool_20x.tsv")
ALL  = os.path.join(T, "all_sfru.tsv")
LL   = os.path.join(T, "ena_latlon.tsv")
OUT  = os.path.join(T, "screen_cohort_out.tsv")


def load_tsv(p, key):
    d = {}
    if not os.path.exists(p):
        print(f"[warn] 缺文件 {p}")
        return d
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r.get(key):
                d[r[key].strip()] = r
    return d


allm = load_tsv(ALL, "run_accession")
llm  = load_tsv(LL, "run") if os.path.exists(LL) else {}

pool = []
with open(POOL, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        pool.append(r)

print("=" * 72)
print(f"候选池总数 = {len(pool)}")
print("=" * 72)

def classify_platform(plat, layout):
    p = (plat or "").upper()
    if "PACBIO" in p or "NANOPORE" in p or "OXFORD" in p:
        return "长读长(剔除)"
    if "BGISEQ" in p or "DNBSEQ" in p:
        return "BGISEQ(短读长,误差谱不同)"
    if "ILLUMINA" in p or "HISEQ" in p or "NOVA" in p or "MISEQ" in p:
        return "Illumina(短读长)"
    return f"其它({plat})"

plat_c = collections.Counter()
layout_c = collections.Counter()
for r in pool:
    plat_c[classify_platform(r.get("platform"), r.get("layout"))] += 1
    layout_c[r.get("layout", "?")] += 1

print("\n--- 平台构成 ---")
for k, v in plat_c.most_common():
    print(f"  {k:<28} {v:>4}  ({v/len(pool)*100:.1f}%)")

print("\n--- layout 构成 ---")
for k, v in layout_c.most_common():
    print(f"  {k:<12} {v:>4}")

# 区域 / 国家
reg_c = collections.Counter(r.get("region", "?") for r in pool)
print("\n--- 区域构成 ---")
for k, v in reg_c.most_common():
    print(f"  {k:<18} {v:>4}  ({v/len(pool)*100:.1f}%)")

ctry_c = collections.Counter((r.get("country") or "?").split(":")[0].strip() for r in pool)
print("\n--- 国家构成（前 20）---")
for k, v in ctry_c.most_common(20):
    print(f"  {k:<24} {v:>4}")

# 剔除长读长 + 统计剩余
short = [r for r in pool if classify_platform(r.get("platform"), r.get("layout")) != "长读长(剔除)"]
ill   = [r for r in short if classify_platform(r.get("platform"), r.get("layout")).startswith("Illumina")]
illp  = [r for r in ill if r.get("layout") == "PAIRED"]

def summ(name, rows):
    rc = collections.Counter(r.get("region", "?") for r in rows)
    print(f"\n--- {name}  n={len(rows)} ---")
    for k, v in rc.most_common():
        print(f"    {k:<18} {v:>4}")

summ("剔除长读长后", short)
summ("仅 Illumina", ill)
summ("仅 Illumina + PAIRED", illp)

# 坐标覆盖
with_ll = sum(1 for r in illp if r["run"] in llm)
print(f"\nIllumina+PAIRED 中，有经纬度的: {with_ll}/{len(illp)}")

# 深度区间统计（usable）
import statistics
if illp:
    us = [float(r["usable_est_x"]) for r in illp if r.get("usable_est_x")]
    if us:
        print(f"usable 深度: 中位 {statistics.median(us):.1f}x  最小 {min(us):.1f}x  最大 {max(us):.1f}x")

# 写出筛选后的表
cols = ["run", "study", "region", "country", "date", "platform", "layout",
        "depth_true_x", "usable_est_x", "sample_total_GB", "download_pct_needed",
        "download_GB_needed"]
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(cols + ["lat", "lon"])
    for r in sorted(illp, key=lambda x: (x.get("region", ""), -(float(x.get("depth_true_x") or 0)))):
        ll = llm.get(r["run"], {})
        lat = ll.get("lat") or ll.get("latitude") or ""
        lon = ll.get("lon") or ll.get("longitude") or ""
        w.writerow([r.get(c, "") for c in cols] + [lat, lon])

print(f"\n[写出] {OUT}  （{len(illp)} 行，已剔除长读长/单端）")
