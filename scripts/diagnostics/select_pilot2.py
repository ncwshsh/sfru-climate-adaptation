#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修正版: SRP544390 的 38 run 实为 S.frugiperda WGS(已核实), 纳入池. 选 6 代表样本(非洲2+中国南2+中国北2)"""
import csv, os
from collections import defaultdict

CSV = r"C:\同步\BaiduSyncdisk\北方民族大学\科研项目\公共数据\气候昆虫基因\昆虫气候基因组\01_数据\00_检索清单\sf_sample_matrix.csv"
rows = list(csv.DictReader(open(CSV, encoding='utf-8-sig')))

# SRP544390 全为 S.frugiperda WGS (已核实), 强制纳入; 其余按 is_wgs=1
def is_wgs_row(r):
    if r['study'] == 'SRP544390': return True   # 已核实为 WGS
    return r.get('is_wgs') == '1'

pool = [r for r in rows if is_wgs_row(r)]
print(f"WGS 池(修正后): {len(pool)}")

SOUTH = {'Hainan','Guangdong','Fujian','Yunnan','Guizhou'}
NORTH = {'Shanxi','Sichuan','Jiangsu','Anhui'}
AFRICA = {'Zambia','Ghana','Rwanda','Malawi','Sudan','Kenya'}

def cls(r):
    g = r['geo'].strip()
    if g in AFRICA: return 'Africa'
    if g == 'China' or g.startswith('China:'):
        prov = g.split(':')[-1].strip() if ':' in g else ''
        if prov in SOUTH: return 'CN_south'
        if prov in NORTH: return 'CN_north'
        return 'CN_other'
    return 'Other'

groups = defaultdict(list)
for r in pool: groups[cls(r)].append(r)
print("分组:", {k:len(v) for k,v in sorted(groups.items())})

def pick(gk, n):
    poolg = groups.get(gk, [])
    # 优先 SRP544390(省粒度), 再 SRP268365; 省/国去重
    by_study = defaultdict(list)
    for r in poolg: by_study[r['study']].append(r)
    chosen, seen = [], set()
    for s in ['SRP544390','SRP268365']:
        for r in by_study.get(s,[]):
            if len(chosen)>=n: break
            loc = r['geo'].split(':')[-1].strip() if ':' in r['geo'] else r['geo']
            if (s,loc) in seen: continue
            seen.add((s,loc)); chosen.append(r)
    if len(chosen)<n:
        have={c['sra_uid'] for c in chosen}
        for s in ['SRP544390','SRP268365']:
            for r in by_study.get(s,[]):
                if len(chosen)>=n: break
                if r['sra_uid'] in have: continue
                have.add(r['sra_uid']); chosen.append(r)
    return chosen[:n]

sel = pick('Africa',2)+pick('CN_south',2)+pick('CN_north',2)
print("\n=== 选定 6 代表样本 ===")
print(f"{'uid':<9}{'study':<11}{'geo':<20}{'year':<9}{'Gb':<7}{'biosample'}")
for r in sel:
    print(f"{r['sra_uid']:<9}{r['study']:<11}{r['geo']:<20}{r['colldate']:<9}{int(r['total_bases'])/1e9:<7.1f}{r['biosample_accn']}")

out = r"C:\SF_data\01_raw\pilot6_download_list.tsv"
with open(out,'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['sra_uid','study','geo','colldate','biosample_accn','total_bases','group'])
    for r in sel:
        g=cls(r); w.writerow([r['sra_uid'],r['study'],r['geo'],r['colldate'],r['biosample_accn'],r['total_bases'],g])
print(f"\n清单: {out}")
# SRR run 号
print("SRR runs: " + ",".join(r['run_list'] for r in sel))
