#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对 01_raw / 01_deep 全量清单做「按样本-读向」分组体检。
目的：判定哪些是可安全删除的孤儿块，哪些残片其实是「还没合成完 / 没成品」的数据。
"""
import os, re, sys
from collections import defaultdict

TSV = r"C:/SF_data/tools/inv_storage.tsv"
GB = 1024**3

BLOCK = re.compile(r"\.part\d+$")
PARTIAL = re.compile(r"\.partial\d+$")

rows = []
with open(TSV, encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        sz, mt, p = parts
        try:
            sz = int(sz)
        except ValueError:
            continue
        rows.append((sz, mt, p))

def norm(p):
    return p.replace("\\", "/")

# 分组
groups = defaultdict(lambda: {"blocks": [], "blocks_sz": 0, "merged": None, "merged_sz": 0,
                              "final": None, "final_sz": 0, "other": []})

for sz, mt, p in rows:
    dirn = os.path.dirname(norm(p))
    fn = os.path.basename(norm(p))
    if fn.startswith("."):
        # 隐藏文件（.blocks_*.txt / .log_*.txt），归 other
        groups[(dirn, "<HIDDEN>")]["other"].append((fn, sz, mt))
        continue
    if BLOCK.search(fn):
        key = BLOCK.sub("", fn)
        k = (dirn, key)
        groups[k]["blocks"].append((fn, sz, mt))
        groups[k]["blocks_sz"] += sz
    elif PARTIAL.search(fn):
        # 可能是残片，也可能本身就是块（.partialN.partM 已在上一条被捕获）
        k = (dirn, fn)
        groups[k]["merged"] = fn
        groups[k]["merged_sz"] = sz
        groups[k].setdefault("_mt", mt)
    elif fn.endswith(".fastq.gz") or fn.endswith(".fq.gz"):
        k = (dirn, fn)
        groups[k]["final"] = fn
        groups[k]["final_sz"] = sz
    else:
        groups[(dirn, fn)]["other"].append((fn, sz, mt))

# 汇总判定
orphan_only = []      # 只有块、无合并体 → 孤儿块（可删）
block_plus_merged = []  # 块 + 合并体 → 块冗余，合并体是数据本体
block_plus_final = []
merged_no_final = []  # 残片无成品 → 要保留（可能是补下起点）
final_only = []
weird = []

for (dirn, key), g in sorted(groups.items()):
    nb = len(g["blocks"]); nbs = g["blocks_sz"]
    mg = g["merged"]; mgs = g["merged_sz"]
    fi = g["final"]; fis = g["final_sz"]
    if nb and not mg and not fi:
        orphan_only.append((dirn, key, nb, nbs))
    elif nb and mg and not fi:
        block_plus_merged.append((dirn, key, nb, nbs, mgs))
    elif nb and not mg and fi:
        block_plus_final.append((dirn, key, nb, nbs, fis))
    elif nb and mg and fi:
        block_plus_merged.append((dirn, key, nb, nbs, mgs))
    elif mg and not fi:
        merged_no_final.append((dirn, key, mgs))
    elif fi and not mg:
        final_only.append((dirn, key, fis))
    elif mg and fi:
        final_only.append((dirn, key, fis))
    elif g["other"] and not (nb or mg or fi):
        weird.append((dirn, key, len(g["other"])))

def rep(title, lst, fmt):
    print(f"\n=== {title}  ({len(lst)} 组) ===")
    tot = 0
    for it in lst[:40]:
        tot += fmt(it)
        print("   ", fmt(it, True))
    if len(lst) > 40:
        print(f"    ... 省略 {len(lst)-40} 组")
    print(f"    [组内合计] {tot/GB:.2f} GB (仅显示前40组之和)")
    return tot

print("#" * 70)
print("# 分组体检结果")
print("#" * 70)
rep("A. 只有孤儿块、无合并体无成品", orphan_only,
    lambda it, s=False: (f"{it[0]}/{it[1]}  块={it[2]}  {it[3]/GB:.3f} GB") if s else 0)
rep("B. 块 + 合并残片（块冗余）", block_plus_merged,
    lambda it, s=False: (f"{it[0]}/{it[1]}  块={it[2]} 块合计={it[3]/GB:.3f} 残片={it[4]/GB:.3f} GB") if s else 0)
rep("C. 块 + 成品（块冗余）", block_plus_final,
    lambda it, s=False: (f"{it[0]}/{it[1]}  块={it[2]} 块合计={it[3]/GB:.3f} 成品={it[4]/GB:.3f} GB") if s else 0)
rep("D. 残片无成品（须保留）", merged_no_final,
    lambda it, s=False: (f"{it[0]}/{it[1]}  残片={it[2]/GB:.3f} GB") if s else 0)
rep("E. 只有成品", final_only,
    lambda it, s=False: (f"{it[0]}/{it[1]}  成品={it[2]/GB:.3f} GB") if s else 0)

# 全局汇总
def tot_blocks(lst, idx):
    return sum(x[idx] for x in lst)

print("\n" + "#" * 70)
print("# 结论汇总")
print("#" * 70)
all_orphan = orphan_only + block_plus_merged + block_plus_final
orphan_files = sum(x[2] for x in all_orphan)
orphan_bytes = tot_blocks(orphan_only, 3) + tot_blocks(block_plus_merged, 3) + tot_blocks(block_plus_final, 3)
print(f"孤儿块文件总数 = {orphan_files} 个, 合计 {orphan_bytes/GB:.2f} GB")
print(f"须保留的残片组 = {len(merged_no_final)} 组, 合计 {tot_blocks(merged_no_final,2)/GB:.2f} GB")
print(f"成品组 = {len(final_only)} 组, 合计 {tot_blocks(final_only,2)/GB:.2f} GB")
print(f"其他(隐藏/日志)组 = {len(weird)} 组")
