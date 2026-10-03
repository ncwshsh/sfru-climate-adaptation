# -*- coding: utf-8 -*-
"""检查 S2 队列中「本地已有残片」能否直接复用。

原理（关键）：
  历史残片是「裁尾后的合法 FASTQ.gz」，即前 N 条完整记录。
  若 N ≥ S2 目标所需记录数 ⇒ **可以直接用，无需重下**（不能追加，但不需要）。
  若不足 ⇒ 只能整份重下（gzip 不能在流中间续写）。

判据：把磁盘字节换算成名义深度
  名义深度 = 磁盘 GB / 0.226        (0.226 GB = 1x)
  目标 = min(真实深度, 25)
  磁盘深度 >= 目标 * 0.98  ->  复用
"""
import csv, os, re, glob, collections

TOOLS = r"C:\SF_data\tools"
RAW = r"C:\SF_data\01_raw"
GPX = 5.65 / 25.0

s2 = list(csv.DictReader(open(os.path.join(TOOLS, "cohort_formal_s2.tsv"),
                             encoding="utf-8"), delimiter="\t"))
byrun = {r["run"]: r for r in s2}

files = collections.defaultdict(dict)
for p in glob.glob(os.path.join(RAW, "*")):
    b = os.path.basename(p)
    m = re.match(r"(SRR\d+)_(\d)\.fastq\.gz(\.partial\d+)?$", b)
    if m:
        files[m.group(1)][m.group(2)] = os.path.getsize(p)
    else:
        m2 = re.match(r"(SRR\d+)_(\d)\.", b)
        if m2 and os.path.isfile(p):
            files[m2.group(1)].setdefault(m2.group(2) + "?", os.path.getsize(p))

ov = sorted(set(files) & set(byrun))
print(f"S2 队列 {len(s2)}｜本地已有 run {len(files)}｜重叠 {len(ov)}\n")
print(f"{'run':<13}{'模块':<5}{'真实x':>8}{'目标x':>7}{'磁盘GB':>9}{'磁盘x':>8}{'判定':>10}")
print("-" * 70)
reuse, redl = [], []
tot_reuse_gb = 0.0
for r in ov:
    rec = byrun[r]
    d = float(rec["depth_x"])
    tgt = min(d, 25.0)
    gb = sum(files[r].values()) / 1e9
    dis = gb / GPX
    ok = dis >= tgt * 0.98
    (reuse if ok else redl).append((r, rec, gb, dis, tgt))
    if ok:
        tot_reuse_gb += float(rec["dl_GB"])
    print(f"{r:<13}{rec['module']:<5}{d:>8.1f}{tgt:>7.1f}{gb:>9.2f}{dis:>8.1f}"
          f"{'✅复用' if ok else '✗重下':>10}")

print("-" * 70)
print(f"可复用 {len(reuse)} 个 → 省下载 {tot_reuse_gb:.1f} GB")
print(f"需重下 {len(redl)} 个")
if reuse:
    print("\n可复用清单（按其模块）:")
    for r, rec, gb, dis, tgt in reuse:
        print(f"  {r}  {rec['module']:<4} 磁盘 {dis:.1f}x / 目标 {tgt:.1f}x  (PCT {rec['pct']}%)")
print("\n需重下清单:")
for r, rec, gb, dis, tgt in redl:
    print(f"  {r}  {rec['module']:<4} 磁盘 {dis:.1f}x / 目标 {tgt:.1f}x  缺 {max(0,tgt-dis):.1f}x"
          f"  (PCT {rec['pct']}%)")
