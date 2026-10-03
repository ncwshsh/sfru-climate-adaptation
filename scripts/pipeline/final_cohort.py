# -*- coding: utf-8 -*-
"""生成正式队列候选表：区分「野外种群 / 实验室株 / 细胞系」，标注待人工补齐项。

判定依据：ENA study_title（见 study_titles.json）+ instrument_platform + depth。
输出 cohort_candidates.tsv
"""
import csv, os, collections

T = r"C:\SF_data\tools"

# study -> (类型, 说明)  类型: FIELD / LAB_STRAIN / CELL_LINE / LAB_EXP / UNKNOWN
CLS = {
    "PRJNA591441": ("FIELD", "AFR2017 非洲+中国野外种群 (CAAS)"),
    "PRJNA1015028": ("FIELD", "塞内加尔寄主适应野外种群 (INRAE)"),
    "PRJNA640063": ("FIELD", "美洲野外种群 (Univ. Tennessee)"),
    "PRJNA1061840": ("FIELD", "马来西亚野外种群 (Monash MY)"),
    "PRJNA545483": ("FIELD", "巴西野外种群 (Bayer)"),
    "PRJNA553264": ("FIELD", "华南野外种群 粤/滇 (BGI)"),
    "PRJNA639295": ("FIELD", "印度/贝宁野外 (INRAE)"),
    "PRJNA590312": ("FIELD", "浙江野外 (浙大)"),
    "PRJEB13173": ("UNKNOWN", "Genoscope,标题残缺待查"),
    "PRJEB13174": ("UNKNOWN", "Genoscope,标题残缺待查"),
    "PRJNA494340": ("LAB_STRAIN", "INRA corn/rice 参考株系"),
    "PRJNA1104617": ("LAB_STRAIN", "spinetoram 抗性株 (ESALQ)"),
    "PRJNA1104299": ("LAB_STRAIN", "敏感株 (ESALQ)"),
    "PRJNA662887": ("LAB_STRAIN", "INRAE 实验室种群 sfC"),
    "PRJNA838271": ("LAB_EXP", "ichnovirus 感染实验 (CNRS)"),
    "PRJNA344686": ("CELL_LINE", "Sf-RVN 细胞系"),
    "PRJNA942085": ("CELL_LINE", "Sf9 landing pad 细胞系"),
    "PRJEB12116": ("CELL_LINE", "SF21 细胞系"),
}

def ne(v):
    v = (v or "").strip()
    return v != "" and not v.lower().startswith("missing")

pool = list(csv.DictReader(open(os.path.join(T, "deep_pool_20x.tsv"),
                                encoding="utf-8"), delimiter="\t"))
meta = {d["run_accession"]: d for d in csv.DictReader(
    open(os.path.join(T, "cand_meta.tsv"), encoding="utf-8"), delimiter="\t")}

rows = []
for r in pool:
    plat = (r.get("platform") or "").upper()
    if "PACBIO" in plat or "NANOPORE" in plat:
        continue
    st = r["study"]
    typ, note = CLS.get(st, ("UNKNOWN", ""))
    m = meta.get(r["run"], {})
    rows.append({
        "run": r["run"], "study": st, "type": typ, "note": note,
        "region": r.get("region", ""), "country": r.get("country", ""),
        "date": r.get("date", ""), "platform": r.get("platform", ""),
        "layout": r.get("layout", ""),
        "depth_true_x": r.get("depth_true_x", ""),
        "usable_est_x": r.get("usable_est_x", ""),
        "total_GB": r.get("sample_total_GB", ""),
        "pct_needed": r.get("download_pct_needed", ""),
        "dl_GB_needed": r.get("download_GB_needed", ""),
        "latlon": m.get("location", "") if ne(m.get("location")) else "",
        "host": m.get("host", ""), "isolation_source": m.get("isolation_source", ""),
        "collection_date_ena": m.get("collection_date", ""),
        "need_coord": "" if ne(m.get("location")) else "Y",
        "need_strain": "" if ne(m.get("host")) and m.get("host", "").lower() not in ("", "missing") else "Y",
    })

cols = ["run", "study", "type", "note", "region", "country", "date", "platform",
        "layout", "depth_true_x", "usable_est_x", "total_GB", "pct_needed",
        "dl_GB_needed", "latlon", "host", "isolation_source",
        "collection_date_ena", "need_coord", "need_strain"]
rows.sort(key=lambda x: (x["type"] != "FIELD", x["region"], x["country"], -float(x["depth_true_x"] or 0)))

out = os.path.join(T, "cohort_candidates.tsv")
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(cols)
    for r in rows:
        w.writerow([r.get(c, "") for c in cols])

print(f"[写出] {out}  {len(rows)} 行\n")
c = collections.Counter(r["type"] for r in rows)
print("=== 类型分布 ===")
for k, v in c.most_common():
    print(f"  {k:<12} {v}")

field = [r for r in rows if r["type"] == "FIELD"]
print(f"\n=== 野外种群 n={len(field)}：按区域/国家 ===")
rc = collections.Counter((r["region"], (r["country"] or "?").split(":")[0].strip()) for r in field)
for (reg, ct), v in sorted(rc.items(), key=lambda x: (x[0][0], -x[1])):
    deep = sum(1 for r in field if r["region"] == reg and (r["country"] or "").split(":")[0].strip() == ct)
    print(f"  {reg:<20} {ct:<16} {deep}")

print(f"\n=== 野外种群：平台 ===")
for k, v in collections.Counter(r["platform"] for r in field).most_common():
    print(f"  {k:<16} {v}")

print(f"\n=== 野外种群：待补项 ===")
print(f"  缺坐标 need_coord=Y  : {sum(1 for r in field if r['need_coord'])}/{len(field)}")
print(f"  缺株系 need_strain=Y : {sum(1 for r in field if r['need_strain'])}/{len(field)}")

print(f"\n=== 野外种群：深度 ===")
import statistics
us = [float(r["usable_est_x"]) for r in field if r["usable_est_x"]]
print(f"  usable 中位 {statistics.median(us):.1f}x  [{min(us):.1f} ~ {max(us):.1f}]")

print("\n=== 野外种群 全部下载量估算 ===")
tot = sum(float(r["dl_GB_needed"] or 0) for r in field)
print(f"  合计 {tot:.1f} GB  ({tot/1000:.2f} TB)，按 2.4 MB/s ≈ {tot*1024/2.4/3600:.0f} 小时")
