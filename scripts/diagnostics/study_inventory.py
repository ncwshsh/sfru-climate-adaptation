# -*- coding: utf-8 -*-
"""study 层清单：把 18 个 study 归拢成"论文线索 + 覆盖情况"表，供决定是否人工补坐标。"""
import csv, os, time, json, urllib.parse, urllib.request, collections

T = r"C:\SF_data\tools"
PROXY = "http://127.0.0.1:7897"
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))

pool = {r["run"]: r for r in csv.DictReader(
    open(os.path.join(T, "deep_pool_20x.tsv"), encoding="utf-8"), delimiter="\t")}

meta = {}
p = os.path.join(T, "cand_meta.tsv")
if os.path.exists(p):
    for d in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"):
        meta[d["run_accession"]] = d

# 补拉失败的 2 个 study
FIELDS = ["run_accession", "sample_accession", "country", "location",
          "collection_date", "host", "isolation_source", "library_layout",
          "instrument_platform"]
for st in ["PRJEB12116", "PRJEB13173"]:
    q = urllib.parse.urlencode({"accession": st, "result": "read_run",
                                "fields": ",".join(FIELDS), "format": "tsv"})
    try:
        with opener.open("https://www.ebi.ac.uk/ena/portal/api/filereport?" + q, timeout=90) as r:
            txt = r.read().decode("utf-8", "replace")
        lines = [l for l in txt.splitlines() if l.strip()]
        hdr = lines[0].split("\t")
        got = 0
        for l in lines[1:]:
            d = dict(zip(hdr, l.split("\t")))
            if d.get("run_accession") in pool:
                meta[d["run_accession"]] = d
                got += 1
        print(f"[补拉] {st} 命中 {got}")
    except Exception as e:
        print(f"[补拉失败] {st}: {e}")

# 重写 cand_meta.tsv
with open(p, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(FIELDS)
    for k, d in meta.items():
        w.writerow([d.get(x, "") for x in FIELDS])

def ne(v):
    v = (v or "").strip()
    return v != "" and not v.lower().startswith("missing")


# study 标题
def study_title(st):
    q = urllib.parse.urlencode({"accession": st, "result": "study",
                                "fields": "study_accession,study_title,first_public,center_name",
                                "format": "tsv"})
    try:
        with opener.open("https://www.ebi.ac.uk/ena/portal/api/filereport?" + q, timeout=60) as r:
            t = r.read().decode("utf-8", "replace")
        ls = [l for l in t.splitlines() if l.strip()]
        return dict(zip(ls[0].split("\t"), ls[1].split("\t"))) if len(ls) > 1 else {}
    except Exception as e:
        return {"study_title": f"<err {e}>"}


by_study = collections.defaultdict(list)
for run, d in meta.items():
    by_study[(pool.get(run, {}).get("study") or d.get("study") or "?")].append(d)

print("\n" + "=" * 100)
print(f"{'study':<15}{'n':>3} {'平台':<20}{'国家(前3)':<34}{'host已知':>7}{'坐标':>5}  日期")
print("=" * 100)
studies = []
for st, rows in sorted(by_study.items(), key=lambda x: -len(x[1])):
    plats = collections.Counter(r.get("instrument_platform", "?") for r in rows)
    ctrys = collections.Counter((r.get("country") or "?").split(":")[0].strip() for r in rows)
    host_known = sum(1 for r in rows if ne(r.get("host")))
    coord = sum(1 for r in rows if ne(r.get("location")))
    dates = sorted({(r.get("collection_date") or "?")[:4] for r in rows})
    dstr = f"{dates[0]}~{dates[-1]}" if len(dates) > 1 else (dates[0] if dates else "?")
    print(f"{st:<15}{len(rows):>3} {str(plats.most_common(1)[0][0]):<20}"
          f"{str([c for c,_ in ctrys.most_common(3)]):<34}{host_known:>5}/{len(rows):<2}"
          f"{coord:>4}  {dstr}")
    studies.append((st, len(rows)))

print("\n=== study 标题（论文线索）===")
for st, n in studies:
    info = study_title(st)
    print(f"\n[{st}] n={n}")
    print(f"  {info.get('study_title','?')}")
    print(f"  首次公开: {info.get('first_public','?')}   中心: {info.get('center_name','?')}")

json.dump({st: study_title(st) for st, _ in studies},
          open(os.path.join(T, "study_titles.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] {os.path.join(T,'study_titles.json')}")
