#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""筛查超深样本（>70x）是否为混池测序 / 细胞系 / 实验室品系。

判据：
  1. sample_title / study_title 含 pool / pooled / bulk / mixed -> 混池，排除
  2. 含 cell / cell line / cells / strain / laboratory -> 非野外个体，排除
  3. 同一 study 内深度普遍极高 -> 可能是特殊实验设计，标记待核
"""
import csv, re, collections

PATH = r"C:\SF_data\tools\sfru_wgs_lib.tsv"
GENOME = 384_000_000
HI = 70.0

rows = []
with open(PATH, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        try:
            d = int(r["base_count"]) / GENOME
        except (ValueError, TypeError):
            continue
        rows.append({**r, "depth": d})

hi = [x for x in rows if x["depth"] > HI]
print(f"总样本 {len(rows)}，深度 >{HI}x 的 {len(hi)} 个\n")

# 注意：不能笼统排除 "strain"——rice/corn host strain 是本项目要研究的宿主株系分层变量，
# 排掉会把关键生物学信息一起丢掉。只排除【近交系/实验室品系】和【细胞系】与【混池】。
BAD = re.compile(
    r"pool(ed)?|bulk|mixed|cell\s*line|\bcells?\b|inbred|"
    r"lab(oratory)?\s*(strain|colony|reared)|reared\s*(in\s*)?lab",
    re.I)

print("=== 逐个核查 >70x 样本 ===")
print(f"{'run':<14}{'深度':>7}  {'判定':<10} {'国家':<22} 线索")
print("-" * 100)
verdicts = collections.Counter()
keep, drop = [], []
for x in sorted(hi, key=lambda x: -x["depth"]):
    txt = f"{x['sample_title']} | {x['study_title']}"
    m = BAD.search(txt)
    if m:
        v = "排除"
        drop.append(x)
    else:
        v = "疑似可用"
        keep.append(x)
    verdicts[v] += 1
    print(f"{x['run_accession']:<14}{x['depth']:>7.0f}x  {v:<10} {x['country'][:20]:<22} {txt[:46]}")

print(f"\n汇总: {dict(verdicts)}")

# 按 study 看超深样本的聚集情况
print("\n=== 超深样本按 study 聚集 ===")
st = collections.defaultdict(list)
for x in hi:
    st[x["study_accession"]].append(x)
for s in sorted(st, key=lambda k: -len(st[k])):
    g = st[s]
    flag = "⚠" if len(g) >= 5 else " "
    print(f"{flag} {s:<16} {len(g):>3} 个超深样本 | 中位深度 {sorted(x['depth'] for x in g)[len(g)//2]:>6.0f}x | {g[0]['study_title'][:40]}")

# 检查所有样本（不限深度）里的细胞系/混池
print("\n=== 全库扫描：非野外个体（细胞系/混池/实验室品系）===")
nonwild = [x for x in rows if BAD.search(f"{x['sample_title']} | {x['study_title']}")]
print(f"命中 {len(nonwild)} 个")
for x in nonwild[:25]:
    print(f"  {x['run_accession']:<14}{x['depth']:>7.1f}x  {x['country'][:18]:<20}{x['sample_title'][:44]}")

with open(r"C:\SF_data\tools\exclude_runs.txt", "w", encoding="utf-8") as f:
    for x in sorted(nonwild, key=lambda x: x["run_accession"]):
        f.write(x["run_accession"] + "\n")
print(f"\n已写出排除名单: C:\\SF_data\\tools\\exclude_runs.txt ({len(nonwild)} 个)")
