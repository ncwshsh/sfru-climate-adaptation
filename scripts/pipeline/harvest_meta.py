# -*- coding: utf-8 -*-
"""批量采集候选池运行记录的元数据（含 host / location / collection_date）。

ENA filereport(read_run) 支持字段：
  run_accession, sample_accession, country, location(latlon), collection_date,
  host, isolation_source, library_layout, instrument_platform
按 study 批量取（sample 端点不支持 study，read_run 支持）。
"""
import csv, os, io, sys, time, urllib.parse, urllib.request

T = r"C:\SF_data\tools"
POOL = os.path.join(T, "deep_pool_20x.tsv")
OUT  = os.path.join(T, "cand_meta.tsv")
PROXY = "http://127.0.0.1:7897"
FIELDS = ["run_accession", "sample_accession", "country", "location",
          "collection_date", "host", "isolation_source", "library_layout",
          "instrument_platform"]

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))

pool = list(csv.DictReader(open(POOL, encoding="utf-8"), delimiter="\t"))
short = [r for r in pool
         if "PACBIO" not in (r.get("platform") or "").upper()
         and "NANOPORE" not in (r.get("platform") or "").upper()]
pool_runs = {r["run"] for r in short}
studies = sorted({r["study"] for r in short})
print(f"候选 {len(short)} 个，涉及 study {len(studies)} 个")


def fetch(study):
    q = urllib.parse.urlencode({
        "accession": study, "result": "read_run",
        "fields": ",".join(FIELDS), "format": "tsv"})
    url = "https://www.ebi.ac.uk/ena/portal/api/filereport?" + q
    for attempt in range(3):
        try:
            with opener.open(url, timeout=90) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            print(f"  [retry {attempt+1}] {study}: {e}")
            time.sleep(3)
    return ""


allrows = []
for i, s in enumerate(studies, 1):
    txt = fetch(s)
    lines = [l for l in txt.splitlines() if l.strip()]
    if len(lines) < 2:
        print(f"[{i}/{len(studies)}] {s:<16} 无数据")
        continue
    hdr = lines[0].split("\t")
    keep = 0
    for l in lines[1:]:
        d = dict(zip(hdr, l.split("\t")))
        if d.get("run_accession") in pool_runs:
            allrows.append(d)
            keep += 1
    print(f"[{i}/{len(studies)}] {s:<16} 命中候选 {keep}")

# 写出
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(FIELDS)
    for d in allrows:
        w.writerow([d.get(k, "") for k in FIELDS])
print(f"\n[写出] {OUT}  {len(allrows)} 行")

# 覆盖率报告
def nonempty(v):
    v = (v or "").strip()
    return v != "" and not v.lower().startswith("missing")

n = len(allrows)
def cov(k):
    c = sum(1 for d in allrows if nonempty(d.get(k)))
    return c, f"{c}/{n} ({c/max(1,n)*100:.1f}%)"

print("\n=== 元数据覆盖率（候选池内）===")
for k in ["sample_accession", "country", "location", "collection_date",
          "host", "isolation_source", "instrument_platform"]:
    c, s = cov(k)
    print(f"  {k:<20} {s}")

import collections
print("\n=== host 取值 ===")
for k, v in collections.Counter((d.get("host") or "(空)") for d in allrows).most_common(12):
    print(f"  {k:<20} {v}")

print("\n=== instrument_platform ===")
for k, v in collections.Counter((d.get("instrument_platform") or "(空)") for d in allrows).most_common():
    print(f"  {k:<16} {v}")

print("\n=== 有 location 的样本 ===")
for d in allrows:
    if nonempty(d.get("location")):
        print(f"  {d['run_accession']:<14} {d.get('country',''):<26} {d.get('location','')}")
