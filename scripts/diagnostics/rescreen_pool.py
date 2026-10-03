# -*- coding: utf-8 -*-
"""按真实深度重筛样本池：找出能达到 usable>=20x 的样本，并算出需要下载多少比例。
usable ~= nominal * 0.6  (实测系数 0.56~0.74，保守取 0.6)
=> 名义深度需 >= 33.3x
读取比例 = 需要的名义深度 / 样本真实深度
"""
import csv, collections

M = r"C:\SF_data\tools\sfru_wgs_matrix.tsv"
GEN = 383_923_118
GB_PER_X = 5.65 / 25.0   # 由库中实测：25x -> 5.65 GB gz（R1+R2）

rows = []
with open(M, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        try:
            d = float(r["depth_x"] or 0)
        except ValueError:
            d = 0.0
        r["_d"] = d
        rows.append(r)

print("总样本 =", len(rows))

# 真实深度分布
bins = [(0,5),(5,10),(10,20),(20,30),(30,40),(40,60),(60,100),(100,1000)]
print("\n=== 真实深度分布（ENA base_count/383.9Mb）===")
for lo,hi in bins:
    n = sum(1 for r in rows if lo <= r["_d"] < hi)
    bar = "#" * int(n/8)
    print(f"  {lo:>4}-{hi:<4}x  n={n:<5} {bar}")

# 目标
TARGET_X = 20/0.6      # 需要下载到的名义深度
print(f"\n=== 目标：usable>=20x  =>  需下载到名义 {TARGET_X:.1f}x ===")

ok = [r for r in rows if r["_d"] >= TARGET_X]
print(f"全库满足（可整份下载到 >= {TARGET_X:.0f}x）的样本: {len(ok)} 个")

# 按区域
print("\n按区域统计（仅列出满足的）:")
reg = collections.Counter()
for r in ok:
    reg[r["region"].split("(")[0].strip()] += 1
for k,v in reg.most_common():
    print(f"  {k:<20} {v}")

# 需要的下载量
print("\n=== 需要的下载量（GB/样本，R1+R2 gz）===")
gb = TARGET_X * GB_PER_X
print(f"  每样本约 {gb:.2f} GB")
print(f"  仅上述 {len(ok)} 个样本全下完 = {gb*len(ok)/1000:.1f} TB")

print("\n=== 现有 pilot 样本：需要补下多少 ===")
pilots = ["SRR10980085","SRR11528381","SRR11528382","SRR12044628",
          "SRR12044633","SRR12044649","SRR31304341","SRR31304345"]
cur = {"SRR10980085":30.3,"SRR11528381":17.0,"SRR11528382":18.4,
       "SRR12044628":16.0,"SRR12044633":20.5,"SRR12044649":30.6,
       "SRR31304341":100.0,"SRR31304345":100.0}
print(f"{'run':<14}{'真实深度':>9}{'已下%':>8}{'已下深度':>9}{'需下%':>8}{'需下GB':>9}  可行?")
byrun = {r["run"]: r for r in rows}
for p in pilots:
    r = byrun.get(p)
    if not r: 
        print(f"{p:<14}{'不在库':>9}"); continue
    d = r["_d"]; c = cur[p]
    have = d*c/100
    need = TARGET_X/d*100
    needgb = max(0, (TARGET_X - have)) * GB_PER_X
    ok_ = "可" if need <= 100 else "深度不足"
    print(f"{p:<14}{d:>8.1f}x{c:>7.1f}%{have:>8.1f}x{need:>7.1f}%{needgb:>8.2f}  {ok_}")
