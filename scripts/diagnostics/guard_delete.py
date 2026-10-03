#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""删除前护栏：只允许删 块(.partN) 与被取代的残片(.partialN)，绝不允许成品"""
import os, re, sys
from collections import Counter

DEL = r"C:/SF_data/tools/delete_list.txt"
KEEP = r"C:/SF_data/tools/keep_list.txt"

OK_BLOCK = re.compile(r"\.part\d+$")
OK_PARTIAL = re.compile(r"\.partial\d+$")
FORBID = re.compile(r"\.(?:fastq|fq)\.gz$")

def to_win(p):
    p = p.replace("\\", "/")
    if re.match(r"^/[a-zA-Z]/", p):
        p = p[1].upper() + ":" + p[2:]
    return p

bad = []; n = 0; tb = 0
byext = Counter(); dirs = Counter(); samples = set()
for line in open(DEL, encoding="utf-8"):
    p = line.strip()
    if not p: continue
    n += 1
    fn = os.path.basename(p)
    try: sz = os.path.getsize(to_win(p))
    except OSError: sz = -1
    if sz < 0:
        bad.append(("MISSING", p)); continue
    tb += sz
    if FORBID.search(fn): bad.append(("FORBIDDEN_FINAL", p))
    elif OK_BLOCK.search(fn): byext["block(.partN)"] += 1
    elif OK_PARTIAL.search(fn): byext["partial(.partialN)"] += 1
    else: bad.append(("UNKNOWN_PATTERN", p))
    dirs[os.path.dirname(p)] += 1
    m = re.match(r"^(SRR\d+)_", fn)
    if m: samples.add(m.group(1))

print(f"清单条数      = {n}")
print(f"实际存在字节  = {tb/1024**3:.2f} GB")
print(f"分类          = {dict(byext)}")
print(f"涉及目录      = {dict(dirs)}")
print(f"涉及样本数    = {len(samples)}")
print(f"护栏异常      = {len(bad)}")
for b in bad[:20]: print("   !!", b)

kn = 0; kb = 0; kfin = 0
for line in open(KEEP, encoding="utf-8"):
    p = line.strip()
    if not p: continue
    kn += 1
    try:
        s = os.path.getsize(to_win(p))
        if s > 0: kb += s
    except OSError: pass
    if re.search(r"\.(fastq|fq)\.gz$", os.path.basename(p)): kfin += 1
print(f"\n保留清单      = {kn} 个, {kb/1024**3:.2f} GB, 其中成品 {kfin} 个")

if bad:
    print("\n!!! 护栏拦截：清单含不允许删除的条目，拒绝执行 !!!"); sys.exit(2)
print("\n✓ 护栏通过：清单中全部为 块(.partN) 或 残片(.partialN)，无任何成品。")
