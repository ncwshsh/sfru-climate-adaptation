# -*- coding: utf-8 -*-
"""队列规模方案：在「下载预算 vs 气候梯度覆盖」之间给出可选档位。

读取 cohort_candidates.tsv（FIELD 子集），按不同规则抽样子集，估算下载量/时长。
带宽按实测 2.4 MB/s（8 并发聚合）计。
"""
import csv, os, collections

T = r"C:\SF_data\tools"
BW = 2.4  # MB/s

rows = [r for r in csv.DictReader(
    open(os.path.join(T, "cohort_candidates.tsv"), encoding="utf-8"), delimiter="\t")
    if r["type"] == "FIELD"]

def gb_per(r):
    return float(r["dl_GB_needed"] or 0)

def report(name, sel):
    tot = sum(gb_per(r) for r in sel)
    print(f"\n【{name}】n={len(sel)}  下载 {tot:.1f} GB ({tot/1000:.2f} TB)  "
          f"≈ {tot*1024/BW/3600:.1f} 小时 ≈ {tot*1024/BW/3600/24:.1f} 天")
    rc = collections.Counter((r["region"], (r["country"] or "?").split(":")[0].strip())
                             for r in sel)
    pc = collections.Counter(r["platform"] for r in sel)
    print("  覆盖: " + " | ".join(
        f"{reg.split('(')[0]}/{ct}={v}" for (reg, ct), v in sorted(rc.items())))
    print("  平台: " + " | ".join(f"{k}={v}" for k, v in pc.most_common()))
    return sel

# 按 (region,country,platform) 分层，取每层深度最高者
def stratified(per_stratum, strata_key="country"):
    by = collections.defaultdict(list)
    for r in rows:
        by[(r["region"], (r["country"] or "?").split(":")[0].strip(), r["platform"])].append(r)
    sel = []
    for k, v in by.items():
        v.sort(key=lambda x: -float(x["usable_est_x"] or 0))
        sel += v[:per_stratum]
    return sel

# 全量
report("A 全量野外池", rows)

# 分层：每 (区域,国家,平台) 最多 N
for n in (5, 10, 15):
    report(f"B 分层每层≤{n}", stratified(n))

# 单层只留 Illumina（独占）
ill_only = [r for r in rows if r["platform"] == "ILLUMINA"]
report("C 仅 Illumina 全量", ill_only)
report("C2 仅 Illumina 分层≤8", stratified(8))

# 亚洲定向：中国+马来西亚全拿
asia = [r for r in rows if r["region"] == "亚洲"]
report("D 亚洲全量（中/马/印）", asia)

# 五区域各取一段梯度：最省
def lean(per_ct=4):
    by = collections.defaultdict(list)
    for r in rows:
        by[(r["country"] or "?").split(":")[0].strip()].append(r)
    sel = []
    for k, v in by.items():
        v.sort(key=lambda x: -float(x["usable_est_x"] or 0))
        sel += v[:per_ct]
    return sel
report("E 精简每国≤4", lean(4))
report("E2 精简每国≤6", lean(6))
