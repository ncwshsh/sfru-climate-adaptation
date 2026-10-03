#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urllib.request, re
PROXY = urllib.request.ProxyHandler({'http':'http://127.0.0.1:7897','https':'http://127.0.0.1:7897'})
opener = urllib.request.build_opener(PROXY)
def get(u):
    return opener.open(urllib.request.Request(u, headers={'User-Agent':'Mozilla/5.0'}), timeout=60).read().decode('utf-8','replace')
for srp in ['SRP544390','SRP268365']:
    print(f"=== /sra/data/{srp}/ ===")
    try:
        txt = get(f'https://ftp.ncbi.nlm.nih.gov/sra/data/{srp}/')
        items = re.findall(r'href="([^"]+)"', txt)
        for d in items[:40]: print(' ', d)
    except Exception as e:
        print('  FAIL', e)
