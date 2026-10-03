#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按「样本-读向 stem」粒度体检存储。
stem 例：SRR10980085_1
artifact：
  final          -> SRR10980085_1.fastq.gz
  partialNN      -> SRR10980085_1.fastq.gz.partial30          (已合并的残片)
  partialNN_block-> SRR10980085_1.fastq.gz.partial30.part0     (残片的块)
  rawpart_block  -> SRR10980085_1.fastq.gz.part0               (无 partial 前缀的块)
"""
import os, re
from collections import defaultdict

TSV = r"C:/SF_data/tools/inv_storage.tsv"
GB = 1024**3

B_FIN = re.compile(r"^(?P<stem>.+?)_(?P<rd>[12])\.(?:fastq|fq)\.gz$")
B_PART = re.compile(r"^(?P<stem>.+?)_(?P<rd>[12])\.(?:fastq|fq)\.gz\.partial(?P<pct>\d+)$")
B_PBLK = re.compile(r"^(?P<stem>.+?)_(?P<rd>[12])\.(?:fastq|fq)\.gz\.partial(?P<pct>\d+)\.part(?P<b>\d+)$")
B_RBLK = re.compile(r"^(?P<stem>.+?)_(?P<rd>[12])\.(?:fastq|fq)\.gz\.part(?P<b>\d+)$")

stems = defaultdict(lambda: defaultdict(lambda: [0, 0, None, None]))  # stem -> kind -> [n, bytes, minmt, maxmt]

def upd(d, kind, sz, mt):
    e = d[kind]
    e[0] += 1; e[1] += sz
    if e[2] is None or mt < e[2]: e[2] = mt
    if e[3] is None or mt > e[3]: e[3] = mt

unmatched = []
for line in open(TSV, encoding="utf-8", errors="replace"):
    line = line.rstrip("\n")
    if not line: continue
    sz, mt, p = line.split("\t", 2)
    sz = int(sz)
    fn = os.path.basename(p.replace("\\", "/"))
    if fn.startswith("."):
        continue
    m = B_PBLK.match(fn)
    if m:
        upd(stems[(m['stem'], m['rd'])], "pb:(p%s)" % m['pct'], sz, mt); continue
    m = B_RBLK.match(fn)
    if m:
        upd(stems[(m['stem'], m['rd'])], "rb", sz, mt); continue
    m = B_PART.match(fn)
    if m:
        upd(stems[(m['stem'], m['rd'])], "P:(p%s)" % m['pct'], sz, mt); continue
    m = B_FIN.match(fn)
    if m:
        upd(stems[(m['stem'], m['rd'])], "FIN", sz, mt); continue
    unmatched.append(fn)

# 判定
CAT = {"DEL_SUPERSEDED": [], "DEL_BLOCKS_ONLY": [], "KEEP": [], "MIXED": []}
for stem, kinds in sorted(stems.items()):
    fin = kinds.get("FIN")
    parts = {k: v for k, v in kinds.items() if k.startswith("P:")}
    pblks = {k: v for k, v in kinds.items() if k.startswith("pb:")}
    rblks = kinds.get("rb")
    rec = (stem, fin, parts, pblks, rblks)
    if fin and (parts or pblks or rblks):
        CAT["DEL_SUPERSEDED"].append(rec)
    elif fin and not (parts or pblks or rblks):
        CAT["KEEP"].append(rec)
    elif not fin and parts and (pblks or rblks):
        CAT["DEL_BLOCKS_ONLY"].append(rec)
    elif not fin and not parts and (pblks or rblks):
        CAT["MIXED"].append(rec)      # 只有块、无残片无成品 -> 数据只在块里
    else:
        CAT["KEEP"].append(rec)

print("#" * 72)
print("# 按 stem 判定")
print("#" * 72)
def show(name, recs, detail, n=16):
    print(f"\n=== {name}  ({len(recs)} 个 stem) ===")
    for r in recs[:n]:
        print("  ", detail(r))
    if len(recs) > n:
        print(f"   ... 省略 {len(recs)-n} 个")

show("① 有成品 + 有残片/块 → 残片与块全部被成品取代，可删",
     CAT["DEL_SUPERSEDED"],
     lambda r: f"{r[0][0]}_{r[0][1]}  FIN={r[1][1]/GB:.3f}GB@{r[1][3]}  " +
               " ".join(f"{k}={v[1]/GB:.3f}GB({v[0]}个)" for k,v in {**r[2],**r[3]}.items()) +
               ("  rb=%d个%.3fGB" % (r[4][0], r[4][1]/GB) if r[4] else ""),
     n=8)

show("② 无成品 + 有残片 + 有块 → 块是残片的冗余副本，可删（保留残片）",
     CAT["DEL_BLOCKS_ONLY"],
     lambda r: f"{r[0][0]}_{r[0][1]}  " +
               " ".join(f"{k}={v[1]/GB:.3f}GB" for k,v in r[2].items()) + "  ||  " +
               " ".join(f"{k}={v[1]/GB:.3f}GB({v[0]}块)" for k,v in r[3].items()),
     n=8)

show("③ 只有块、无残片无成品 → 数据仅在块中，**不可删**（需先合并或补下覆盖）",
     CAT["MIXED"],
     lambda r: f"{r[0][0]}_{r[0][1]}  " +
               " ".join(f"{k}={v[1]/GB:.3f}GB({v[0]}块)" for k,v in r[3].items()) +
               ("  rb=%d块%.3fGB" % (r[4][0], r[4][1]/GB) if r[4] else ""),
     n=20)

# 汇总
def summ(name, recs):
    nbytes = 0; nfiles = 0
    for r in recs:
        for k, v in list(r[2].items()) + list(r[3].items()):
            nbytes += v[1]; nfiles += v[0]
        if r[4]:
            nbytes += r[4][1]; nfiles += r[4][0]
    print(f"{name}: {len(recs)} stem, {nfiles} files, {nbytes/GB:.2f} GB")
    return nbytes, nfiles

print("\n" + "#" * 72)
print("# 汇总")
print("#" * 72)
a = summ("① 可删（被成品取代）", CAT["DEL_SUPERSEDED"])
print(f"   其中: 残片本身 + 块 全部计入")
b = summ("② 可删（块冗余，保留残片）", CAT["DEL_BLOCKS_ONLY"])
c = summ("③ 不可删（数据仅在块中）", CAT["MIXED"])
k = summ("④ 保留（仅成品）", CAT["KEEP"])

# 只算真正"块"的字节
blk_bytes = 0; blk_files = 0
allb = CAT["DEL_SUPERSEDED"] + CAT["DEL_BLOCKS_ONLY"] + CAT["MIXED"]
for r in allb:
    for kk, vv in r[3].items():
        blk_bytes += vv[1]; blk_files += vv[0]
    if r[4]:
        blk_bytes += r[4][1]; blk_files += r[4][0]
print(f"\n>> 全部 .partN 块: {blk_files} files, {blk_bytes/GB:.2f} GB")
safe_blk = 0; safe_blk_n = 0
for r in CAT["DEL_SUPERSEDED"] + CAT["DEL_BLOCKS_ONLY"]:
    for kk, vv in r[3].items():
        safe_blk += vv[1]; safe_blk_n += vv[0]
    if r[4]:
        safe_blk += r[4][1]; safe_blk_n += r[4][0]
print(f">> 其中【安全可删】块: {safe_blk_n} files, {safe_blk/GB:.2f} GB")
print(f">> 另加①组的残片本体:")
sp = 0; spn = 0
for r in CAT["DEL_SUPERSEDED"]:
    for kk, vv in r[2].items():
        sp += vv[1]; spn += vv[0]
print(f"   {spn} files, {sp/GB:.2f} GB")
print(f"\n>> 总可回收 ≈ {(safe_blk+sp)/GB:.2f} GB")
print(f"unmatched(跳过) = {len(unmatched)}")
