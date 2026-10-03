#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验真 + 生成删除/保留清单"""
import os, re
from collections import defaultdict

TSV = r"C:/SF_data/tools/inv_storage.tsv"
GB = 1024**3
B_FIN = re.compile(r"^(?P<stem>.+?)_(?P<rd>[12])\.(?:fastq|fq)\.gz$")
B_PART = re.compile(r"^(?P<stem>.+?)_(?P<rd>[12])\.(?:fastq|fq)\.gz\.partial(?P<pct>\d+)$")
B_PBLK = re.compile(r"^(?P<stem>.+?)_(?P<rd>[12])\.(?:fastq|fq)\.gz\.partial(?P<pct>\d+)\.part(?P<b>\d+)$")
B_RBLK = re.compile(r"^(?P<stem>.+?)_(?P<rd>[12])\.(?:fastq|fq)\.gz\.part(?P<b>\d+)$")

stems = defaultdict(lambda: {"FIN": None, "P": {}, "PB": {}, "RB": []})
paths = {"FIN": {}, "P": defaultdict(list), "PB": defaultdict(list), "RB": defaultdict(list)}
for line in open(TSV, encoding="utf-8", errors="replace"):
    line = line.rstrip("\n")
    if not line: continue
    sz, mt, p = line.split("\t", 2); sz = int(sz)
    fn = os.path.basename(p.replace("\\", "/"))
    if fn.startswith("."): continue
    m = B_PBLK.match(fn)
    if m:
        k = (m['stem'], m['rd']); pk = (m['stem'], m['rd'], m['pct'])
        stems[k]["PB"].setdefault(m['pct'], [0,0]); stems[k]["PB"][m['pct']][0]+=1; stems[k]["PB"][m['pct']][1]+=sz
        paths["PB"][pk].append(p); continue
    m = B_RBLK.match(fn)
    if m:
        k = (m['stem'], m['rd']); stems[k]["RB"].append(sz); paths["RB"][k].append(p); continue
    m = B_PART.match(fn)
    if m:
        k = (m['stem'], m['rd']); stems[k]["P"][m['pct']] = sz
        paths["P"][(m['stem'], m['rd'], m['pct'])].append(p); continue
    m = B_FIN.match(fn)
    if m:
        k = (m['stem'], m['rd']); stems[k]["FIN"] = sz; paths["FIN"][k] = p; continue

DEL = []   # 安全删除的文件路径
KEEP = []  # 必须保留
REPORT = []
bad = 0

for k, g in sorted(stems.items()):
    fin = g["FIN"]; P = g["P"]; PB = g["PB"]; RB = g["RB"]
    if fin is not None and (P or PB or RB):
        # ① 成品取代
        for pct, psz in P.items():
            ok = fin >= psz
            if not ok: bad += 1
            REPORT.append((k, "①FIN>P", f"FIN={fin/GB:.3f} P{pct}={psz/GB:.3f} 差={100*(fin-psz)/max(psz,1):+.1f}% {'OK' if ok else '!!FIN更小'}"))
            DEL += paths["P"][(k[0],k[1],pct)]
        for pct, (n, b) in PB.items():
            REPORT.append((k, "①FIN>PB", f"FIN={fin/GB:.3f} PB{pct}={b/GB:.3f}({n}块)  {'OK' if fin>=b else '!!'}"))
            DEL += paths["PB"][(k[0],k[1],pct)]
        for p in paths["RB"].get(k, []):
            DEL.append(p)
    elif fin is None and P and (PB or RB):
        # ② 块冗余
        for pct, psz in P.items():
            nb, nb_b = PB.get(pct, (0, 0))
            exact = (nb_b == psz) and nb > 0
            if not exact: bad += 1
            REPORT.append((k, "②P=ΣPB" if exact else "②!!不等", f"P{pct}={psz/GB:.4f} ΣPB={nb_b/GB:.4f}({nb}块) Δ={nb_b-psz}B"))
            if exact:
                DEL += paths["PB"][(k[0],k[1],pct)]
            else:
                pass  # 不等就不删，保守
            KEEP.append(paths["P"][(k[0],k[1],pct)][0])
        for p in paths["RB"].get(k, []):
            KEEP.append(p)
    elif fin is None and not P and (PB or RB):
        # ③ 数据仅在块中
        for pct,(n,b) in PB.items(): KEEP += paths["PB"][(k[0],k[1],pct)]
        KEEP += paths["RB"].get(k, [])
    else:
        if fin: KEEP.append(paths["FIN"][k])

print("### 验真结果 ###")
badline = [r for r in REPORT if "!!" in r[1] or "!!" in r[2]]
print(f"异常条目 = {len(badline)}")
for r in badline[:30]:
    print("  !!", r[0], r[1], r[2])

n1 = len([r for r in REPORT if r[1].startswith("①")])
n2 = len([r for r in REPORT if r[1].startswith("②")])
print(f"\n① 成品取代 组 = {n1}")
print(f"② 块冗余   组 = {n2}")

print("\n### ① 差分比分布（FIN vs P，取最小/最大/中位） ###")
import statistics
diffs = []
for k, g in stems.items():
    if g["FIN"] is not None and g["P"]:
        for pct, psz in g["P"].items():
            diffs.append(100*(g["FIN"]-psz)/psz)
if diffs:
    diffs.sort()
    print(f"  n={len(diffs)} min={diffs[0]:.1f}%  p25={diffs[len(diffs)//4]:.1f}%  med={statistics.median(diffs):.1f}%  max={diffs[-1]:.1f}%")
    print(f"  其中 FIN<P 的个数 = {len([d for d in diffs if d<0])}")

# 输出清单
with open(r"C:/SF_data/tools/delete_list.txt","w",encoding="utf-8") as f:
    for p in sorted(set(DEL)): f.write(p + "\n")
with open(r"C:/SF_data/tools/keep_list.txt","w",encoding="utf-8") as f:
    for p in sorted(set(KEEP)): f.write(p + "\n")

def tot(lst):
    t=0
    for p in lst:
        fn = os.path.basename(p)
    return len(lst)

print("\n### 清单 ###")
print(f"delete_list.txt : {len(DEL)} 个文件")
print(f"keep_list.txt   : {len(KEEP)} 个文件")

# 按目录统计删除清单
from collections import Counter
cd = Counter(os.path.dirname(p.replace('\\','/')) for p in DEL)
for d, n in cd.items(): print(f"   删 {d} : {n}")
