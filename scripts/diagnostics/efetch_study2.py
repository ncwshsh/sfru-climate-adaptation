#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多通道核实 SRP544390/SRP268365 测序策略"""
import urllib.request, urllib.parse, time, re
UA = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
def get(url, t=60):
    req = urllib.request.Request(url, headers=UA)
    for a in range(3):
        try:
            with urllib.request.urlopen(req, timeout=t) as r:
                return r.read().decode('utf-8','replace')
        except Exception as e:
            if a<2: time.sleep(2); continue
            raise

# 通道1: bioproject db (study 元数据)
for study in ['SRP544390','SRP268365']:
    print(f"=== {study} via bioproject ===")
    try:
        u = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(
            {'db':'bioproject','id':study,'retmode':'xml'})
        txt = get(u)
        for pat,lab in [(r'<Title>([^<]*)</Title>','Title'),(r'<Description>([^<]*)</Description>','Desc'),
                        (r'<ProjectType[^>]*>([^<]*)','Type')]:
            m = re.findall(pat, txt, re.I)
            if m: print(f"  {lab}: {m[:3]}")
        for kw in ['WGS','whole genome','genome sequencing','RNA-seq','transcriptome','Small RNA','Amplicon','resequencing','genome resequencing']:
            if kw.lower() in txt.lower(): print(f"  [kw] {kw}")
    except Exception as e:
        print(f"  FAIL bioproject: {e}")
    time.sleep(0.5)

# 通道2: 直接查一个 SRP544390 的 run (SRR31304341) 在 sra db 的 esummary
print("=== run SRR31304341 esummary (SRP544390 成员) ===")
try:
    u = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode(
        {'db':'sra','id':'SRR31304341','retmode':'json'})
    d = __import__('json').loads(get(u))
    r = d.get('result',{}).get('SRR31304341',{})
    for k in ['title','strategy','type','srcorg','libraryname','platform','instrument']:
        print(f"  {k}: {r.get(k,'')}")
except Exception as e:
    print(f"  FAIL: {e}")
