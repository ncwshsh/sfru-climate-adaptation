#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测 SRR31304341 在 ftp.ncbi.nlm.nih.gov/sra/ 的文件位置, 并测试下载可达性"""
import urllib.request, urllib.parse, re, socket
UA={'User-Agent':'Mozilla/5.0'}
PROXY = urllib.request.ProxyHandler({'http':'http://127.0.0.1:7897','https':'http://127.0.0.1:7897'})
opener = urllib.request.build_opener(PROXY)

srr='SRR31304341'
nums=srr[3:]  # '31304341'
sub=f"SR/R{nums[:2]}/{nums[2:]}"
cands = [
  f"https://ftp.ncbi.nlm.nih.gov/sra/sra-infmt/{sub}/{srr}.SRA",
  f"https://ftp.ncbi.nlm.nih.gov/sra/sra-infmt/{sub}/{srr}.sra",
  f"https://ftp.ncbi.nlm.nih.gov/sra/sra-infmt/{sub}/",
  f"https://ftp.ncbi.nlm.nih.gov/sra/sra/{sub}/{srr}.SRA",
]
for u in cands:
    try:
        if u.endswith('.SRA'):
            r = opener.open(urllib.request.Request(u, method='HEAD', headers=UA), timeout=30)
            print(f"OK  {u}  size={r.headers.get('Content-Length')}")
        else:
            r = opener.open(urllib.request.Request(u, headers=UA), timeout=30)
            txt=r.read(2000).decode('utf-8','replace')
            files=re.findall(r'href="([^"]+)"', txt)
            print(f"DIR {u}")
            for f in files[:20]: print("   ", f)
    except Exception as e:
        print(f"FAIL {u} -> {e}")
