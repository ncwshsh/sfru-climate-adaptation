#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urllib.request, re
PROXY = urllib.request.ProxyHandler({'http':'http://127.0.0.1:7897','https':'http://127.0.0.1:7897'})
opener = urllib.request.build_opener(PROXY)
def get(u):
    return opener.open(urllib.request.Request(u, headers={'User-Agent':'Mozilla/5.0'}), timeout=40).read().decode('utf-8','replace')
txt = get('https://ftp.ncbi.nlm.nih.gov/sra/')
dirs = re.findall(r'href="([^"]+)"', txt)
print('=== /sra/ 条目 ===')
for d in dirs[:50]: print(' ', d)
