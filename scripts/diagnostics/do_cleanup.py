#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单进程删除删除清单中仍存在的文件（避免逐文件 spawn 进程）"""
import os, re, sys, time

DEL = r"C:/SF_data/tools/delete_list.txt"

def to_win(p):
    p = p.replace("\\", "/")
    if re.match(r"^/[a-zA-Z]/", p):
        p = p[1].upper() + ":" + p[2:]
    return p

# 护栏：再次确认不含成品
FORBID = re.compile(r"\.(?:fastq|fq)\.gz$")
paths = []
with open(DEL, encoding="utf-8") as f:
    for line in f:
        p = line.strip()
        if not p: continue
        if FORBID.search(os.path.basename(p)):
            print("!! 清单含成品，中止:", p); sys.exit(2)
        paths.append(to_win(p))

t0 = time.time()
exist = 0; removed = 0; freed = 0; missing = 0; err = 0
for i, p in enumerate(paths):
    if not os.path.exists(p):
        missing += 1; continue
    exist += 1
    try:
        sz = os.path.getsize(p)
        os.remove(p)
        removed += 1; freed += sz
    except OSError as e:
        err += 1
        if err <= 5: print("  ERR", p, e)
    if (i+1) % 1000 == 0:
        print(f"  ... 已扫 {i+1}/{len(paths)}, 删除 {removed}, 释放 {freed/1024**3:.2f} GB, 用时 {time.time()-t0:.0f}s")

t1 = time.time()
print(f"\n清单条目     = {len(paths)}")
print(f"仍存在并删除 = {removed}  ({removed/exist*100:.1f}% of existing)")
print(f"已不存在     = {missing}")
print(f"错误         = {err}")
print(f"释放空间     = {freed/1024**3:.2f} GB")
print(f"耗时         = {t1-t0:.1f}s")

def cnt(d):
    try: return len([x for x in os.listdir(d)])
    except OSError: return -1
print(f"\n01_raw 现有条目 = {cnt(r'C:/SF_data/01_raw')}")
print(f"01_deep 现有条目 = {cnt(r'C:/SF_data/01_deep')}")
