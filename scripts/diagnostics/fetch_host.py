# -*- coding: utf-8 -*-
"""fetch_host.py —— 从 NCBI SRA/BioSample 抓每个 run 的"寄主/株系"等属性

为什么需要它：草地贪夜蛾分**玉米型（corn strain）和水稻型（rice strain）**，
两个株系在寄主偏好、迁飞、甚至气候适应上都不同。若株系与纬度相关，
不控制它就会把"寄主适应"误读成"气候适应"。

用法（WSL gea 环境，需代理）:
  python /mnt/c/SF_data/tools/fetch_host.py [样本数上限]
输出: /mnt/c/SF_data/tools/report/host_sra.tsv
"""
import os
import re
import sys
import time
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

PROXY = os.environ.get("http_proxy") or "http://127.0.0.1:8830"
opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
opener.addheaders = [("User-Agent", "sfru-project/1.0")]

BAMLIST = "/mnt/c/SF_data/tools/bamlist_keep214.txt"
OUT = "/mnt/c/SF_data/tools/report/host_sra.tsv"
CACHE = "/mnt/c/SF_data/tools/report/.sra_xml_cache"
os.makedirs(CACHE, exist_ok=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def get(url, tries=3):
    for i in range(tries):
        try:
            with opener.open(url, timeout=40) as r:
                return r.read()
        except Exception as e:
            if i == tries - 1:
                return b""
            time.sleep(2 + 2 * i)
    return b""


def uid_of(run):
    u = EUTILS + "esearch.fcgi?db=sra&retmode=json&term=" + urllib.parse.quote(run)
    d = get(u)
    try:
        return json.loads(d)["esearchresult"]["idlist"][0]
    except Exception:
        return None


def parse_xml(run, xml_bytes):
    """返回 (biosample, {tag: value})"""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return "", {}
    attrs = {}
    bio = ""
    for a in root.iter("SAMPLE_ATTRIBUTE"):
        t = a.findtext("TAG") or ""
        v = a.findtext("VALUE") or ""
        if t and v:
            attrs[t.strip()] = v.strip()
    m = re.search(rb"<BioSample[^>]*>([^<]+)</BioSample>", xml_bytes)
    if m:
        bio = m.group(1).decode()
    if not bio:
        for ext in root.iter("EXTERNAL_ID"):
            if (ext.get("namespace") or "").lower() == "biosample":
                bio = ext.text or ""
    return bio, attrs


def main():
    runs = [os.path.basename(l.strip()).split(".")[0]
            for l in open(BAMLIST) if l.strip()]
    if len(sys.argv) > 1:
        runs = runs[: int(sys.argv[1])]
    print("样本 %d 个，开始抓 SRA 属性" % len(runs))

    keys_seen = set()
    recs = []
    for i, run in enumerate(runs, 1):
        cf = os.path.join(CACHE, run + ".xml")
        data = b""
        if os.path.exists(cf) and os.path.getsize(cf) > 100:
            data = open(cf, "rb").read()
        else:
            uid = uid_of(run)
            time.sleep(0.34)
            if uid:
                data = get(EUTILS + "efetch.fcgi?db=sra&id=" + uid)
                open(cf, "wb").write(data)
            time.sleep(0.34)
        bio, attrs = parse_xml(run, data)
        keys_seen.update(attrs.keys())
        recs.append((run, bio, attrs))
        if i % 20 == 0:
            print("  ...%d/%d" % (i, len(runs)))

    # 写表：每行一个样本，列 = 所有出现过的属性名（挑常见的优先）
    pref = ["host", "host_strain", "strain", "cultivar", "host_cultivar", "tissue",
            "dev_stage", "sex", "collected_by", "geo_loc_name", "isolate", "breed"]
    cols = [c for c in pref if c in keys_seen] + sorted(k for k in keys_seen if k not in pref)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("run\tbiosample\t" + "\t".join(cols) + "\n")
        for run, bio, attrs in recs:
            fh.write(run + "\t" + bio + "\t" + "\t".join(attrs.get(c, "") for c in cols) + "\n")
    print("已写出: %s" % OUT)
    print("出现过的属性字段: %s" % ", ".join(sorted(keys_seen)))

    # 重点看 host / strain
    print()
    print("=== 寄主/株系字段统计 ===")
    for c in cols:
        if c in ("host", "host_strain", "strain", "cultivar", "host_cultivar", "isolate"):
            vals = {}
            for run, bio, attrs in recs:
                v = attrs.get(c, "")
                vals[v or "(空)"] = vals.get(v or "(空)", 0) + 1
            print("  %s:" % c)
            for v, n in sorted(vals.items(), key=lambda x: -x[1]):
                print("      %-28s %d" % (v, n))


if __name__ == "__main__":
    main()
