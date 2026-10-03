#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""efetch 拉 SRP544390 的 SRA XML，确认真实测序策略"""
import urllib.request, urllib.parse, time, re
UA = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    for a in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode('utf-8','replace')
        except Exception as e:
            if a<2: time.sleep(2); continue
            raise

# efetch SRA study -> XML
for study in ['SRP544390','SRP268365']:
    u = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(
        {'db':'sra','id':study,'rettype':'docsum'})
    print(f"=== {study} (efetch docsum) ===")
    try:
        txt = get(u)
        # 找 strategy / assay / library strategy
        for pat in [r'<Strategy>([^<]*)</Strategy>', r'strategy="([^"]*)"',
                    r'<Assay>([^<]*)</Assassay>', r'<Assay>([^<]*)</Assay>',
                    r'<Title>([^<]*)</Title>', r'<SourceName>([^<]*)</SourceName>']:
            m = re.findall(pat, txt)
            if m: print(f"  {pat.split('(')[0].strip('<').strip('>')}: {list(set(m))[:6]}")
        # 直接搜关键词
        for kw in ['WGS','whole genome','genome sequencing','RNA','transcriptome','Small RNA','Amplicon','resequencing']:
            if kw.lower() in txt.lower():
                print(f"  [contains] {kw}")
    except Exception as e:
        print(f"  FAIL: {e}")
    time.sleep(0.5)
