#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核实 SRP544390/SRP268365 测序策略 + 从样本矩阵做三段式地理分层抽样(6代表样本)"""
import urllib.request, urllib.parse, json, time, csv, io, re, sys

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            if attempt < 2:
                time.sleep(1.5); continue
            raise

# --- 1. 核实 study 测序策略 ---
def study_meta(study):
    u = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode(
        {'db':'sra','term':study,'retmode':'json','retmax':5})
    d = json.loads(get(u))
    ids = d.get('esearchresult',{}).get('id',[])
    if not ids: return None
    time.sleep(0.45)
    u2 = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode(
        {'db':'sra','id':','.join(ids[:5]),'retmode':'json'})
    d2 = json.loads(get(u2))
    res = d2.get('result',{})
    out = []
    for i in ids[:5]:
        r = res.get(i,{})
        out.append({'id':i,'title':r.get('title',''),'strategy':r.get('strategy',''),
                    'type':r.get('type',''),'srcorg':r.get('srcorg','')})
    return out

print("=== SRP544390 study runs ===")
for r in (study_meta('SRP544390') or []):
    print(f"  {r['id']}: strat={r['strategy']!r} type={r['type']!r} org={r['srcorg']!r}")
    print(f"      title={r['title'][:90]}")
time.sleep(0.5)
print("=== SRP268365 study runs (前5) ===")
for r in (study_meta('SRP268365') or []):
    print(f"  {r['id']}: strat={r['strategy']!r} type={r['type']!r} org={r['srcorg']!r}")
    print(f"      title={r['title'][:90]}")

# --- 2. 地理分层抽样：从 sf_sample_matrix.csv 选 6 代表样本 ---
# 三段式: 非洲热带 / 中国南方(热带-亚热带) / 中国北方(温带)
# 优先 SRP544390(有省粒度) + SRP268365
CSV = r"C:\同步\BaiduSyncdisk\北方民族大学\科研项目\公共数据\气候昆虫基因\昆虫气候基因组\01_数据\00_检索清单\sf_sample_matrix.csv"
rows = list(csv.DictReader(open(CSV, encoding='utf-8-sig')))
print(f"\n矩阵总行数: {len(rows)}")

# 只取 WGS (is_wgs=1)
wgs = [r for r in rows if r.get('is_wgs')=='1']
print(f"WGS 行数: {len(wgs)}")

def geo_class(geo):
    g = geo.strip()
    if g.startswith('China'):
        # 南方省
        south = {'Hainan','Guangdong','Fujian','Yunnan'}
        north = {'Shanxi','Sichuan','Jiangsu','Guizhou','Anhui'}
        if g in ('China','China:'):  return 'CN_other'
        prov = g.split(':')[-1].strip() if ':' in g else g
        if prov in south: return 'CN_south'
        if prov in north: return 'CN_north'
        return 'CN_other'
    # 非洲
    africa = {'Ghana','Zambia','Rwanda','Malawi','Sudan','Kenya','Malaysia'}
    if g in ('Zambia','Ghana','Rwanda','Malawi','Sudan','Kenya'): return 'Africa'
    return 'Other'

from collections import defaultdict
groups = defaultdict(list)
for r in wgs:
    groups[geo_class(r['geo'])].append(r)
print("\n地理分组:")
for k in sorted(groups):
    print(f"  {k}: {len(groups[k])}")

# 选样本: 非洲2 + 中国南2 + 中国北2, 优先 SRP544390(省粒度) 覆盖不同省, 其次 SRP268365
def pick(group_key, n, prefer_study='SRP544390'):
    pool = groups.get(group_key, [])
    # 按 study 分层 + 按省去重
    by_study = defaultdict(list)
    for r in pool:
        by_study[r['study']].append(r)
    ordered_studies = [s for s in [prefer_study,'SRP268365'] if s in by_study]
    chosen = []
    seen_prov = set()
    for s in ordered_studies:
        for r in by_study[s]:
            if len(chosen) >= n: break
            prov = r['geo'].split(':')[-1].strip()
            key = (s, prov)
            # 尽量不同省
            if key in seen_prov: continue
            seen_prov.add(key)
            chosen.append(r)
    # 不足则放宽省限制
    if len(chosen) < n:
        seen_run = {c['sra_uid'] for c in chosen}
        for s in ordered_studies:
            for r in by_study[s]:
                if len(chosen) >= n: break
                if r['sra_uid'] in seen_run: continue
                seen_run.add(r['sra_uid']); chosen.append(r)
    return chosen[:n]

sel = pick('Africa',2) + pick('CN_south',2) + pick('CN_north',2)
print("\n=== 选定 6 代表样本 ===")
print(f"{'sra_uid':<10}{'study':<12}{'geo':<22}{'year':<10}{'bases_Gb':<10}{'biosample'}")
for r in sel:
    gb = int(r['total_bases'])/1e9
    print(f"{r['sra_uid']:<10}{r['study']:<12}{r['geo']:<22}{r['colldate']:<10}{gb:<10.1f}{r['biosample_accn']}")

# 写下载清单
out = r"C:\SF_data\01_raw\pilot6_download_list.tsv"
import os; os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out,'w',newline='',encoding='utf-8') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['sra_uid','study','geo','colldate','biosample_accn','total_bases','group'])
    for r in sel:
        g = 'Africa' if geo_class(r['geo'])=='Africa' else ('CN_south' if geo_class(r['geo'])=='CN_south' else 'CN_north')
        w.writerow([r['sra_uid'],r['study'],r['geo'],r['colldate'],r['biosample_accn'],r['total_bases'],g])
print(f"\n下载清单已写: {out}")
