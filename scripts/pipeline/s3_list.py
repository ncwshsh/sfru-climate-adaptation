#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""经代理 + DoH 解析, 用 S3 ListObjects 找 SRR31304341 在 sra-pub-run-* 桶的文件"""
import urllib.request, urllib.parse, json, re, socket, ssl
PROXY = urllib.request.ProxyHandler({'http':'http://127.0.0.1:7897','https':'http://127.0.0.1:7897'})

# DoH 解析 S3 端点 IP
def doh_resolve(name):
    u = f"https://dns.google/resolve?name={name}&type=A"
    req = urllib.request.Request(u, headers={'User-Agent':'Mozilla/5.0'})
    d = json.load(urllib.request.urlopen(req, timeout=20))
    return [a['data'] for a in d.get('Answer',[]) if a.get('type')==1]

srr='SRR31304341'
# S3 ListObjects: https://{bucket}.s3.amazonaws.com/?prefix={srr}&list-type=2
for bucket in [f'sra-pub-run-{i}' for i in range(1,5)]:
    host=f"{bucket}.s3.amazonaws.com"
    try:
        ips = doh_resolve(host)
        if not ips: print(f"{bucket}: no DoH ips"); continue
        # 用 IP 直连(Host header 仍为 host), 走代理
        url=f"https://{host}/?prefix={srr}&max-keys=20"
        req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0','Host':host})
        r=PROXY.open(req, timeout=30) if hasattr(PROXY,'open') else None
        # 用 opener
        opener=urllib.request.build_opener(PROXY)
        r=opener.open(req, timeout=30)
        txt=r.read().decode('utf-8','replace')
        keys=re.findall(r'<Key>([^<]+)</Key>', txt)
        print(f"{bucket} ({ips[0]}): {len(keys)} keys")
        for k in keys[:10]: print("   ", k)
        if keys: break
    except Exception as e:
        print(f"{bucket} FAIL: {e}")
