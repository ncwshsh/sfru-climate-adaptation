# -*- coding: utf-8 -*-
"""生成深样本候选池清单：真实深度可满足 usable>=20x 的样本 + 需要的下载量。
usable ~= nominal * 0.6  ->  目标名义深度 33.3x
"""
import csv, os

M = r"C:\SF_data\tools\sfru_wgs_matrix.tsv"
OUT = r"C:\SF_data\tools\deep_pool_20x.tsv"
GEN = 383_923_118
GB_PER_X = 5.65 / 25.0     # 库内实测：25x -> 5.65 GB gz（R1+R2）
TARGET = 20 / 0.6          # 33.33x

rows = []
with open(M, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        try:
            d = float(r.get("depth_x") or 0)
        except ValueError:
            d = 0.0
        if d >= TARGET:
            r["_d"] = d
            rows.append(r)

# 已有本地数据的样本（含已下比例）
have = {
    "SRR10980085": 30.3, "SRR11528381": 17.0, "SRR11528382": 18.4,
    "SRR12044628": 16.0, "SRR12044633": 20.5, "SRR12044649": 30.6,
}

rows.sort(key=lambda r: (r["region"], -r["_d"]))

with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["run", "study", "region", "country", "date", "platform", "layout",
                "depth_true_x", "usable_est_x", "sample_total_GB",
                "download_pct_needed", "download_GB_needed", "local_have_pct",
                "local_have_x", "extra_GB_needed"])
    for r in rows:
        d = r["_d"]
        usable = d * 0.6
        total_gb = d * GB_PER_X
        pct = min(100.0, TARGET / d * 100)
        need_gb = total_gb * pct / 100
        hp = have.get(r["run"], 0.0)
        have_x = d * hp / 100
        extra = max(0.0, need_gb - total_gb * hp / 100)
        w.writerow([
            r["run"], r["study"], r["region"], r["country"], r.get("date", ""),
            r.get("platform", ""), r.get("layout", ""),
            f"{d:.1f}", f"{usable:.1f}", f"{total_gb:.2f}",
            f"{pct:.1f}", f"{need_gb:.2f}",
            (f"{hp:.1f}" if hp else ""), (f"{have_x:.1f}" if hp else ""),
            (f"{extra:.2f}" if hp else ""),
        ])

print(f"写入 {OUT}")
print(f"候选样本数 = {len(rows)}")
print(f"每样本需下载约 {TARGET*GB_PER_X:.2f} GB，全池合计 {TARGET*GB_PER_X*len(rows)/1000:.2f} TB")

import collections
c = collections.Counter(r["region"] for r in rows)
print("\n按 region：")
for k, v in c.most_common():
    print(f"  {k:<22} {v}")

c2 = collections.Counter(r["country"] for r in rows)
print("\n按国家（前 15）：")
for k, v in c2.most_common(15):
    print(f"  {k:<28} {v}")

print("\n=== 已有本地数据的样本补下清单 ===")
byrun = {r["run"]: r for r in rows}
for k, p in have.items():
    r = byrun.get(k)
    if not r:
        print(f"  {k}: 真实深度不足 {TARGET:.1f}x，已剔除")
        continue
    d = r["_d"]; total = d * GB_PER_X
    need = total * min(100.0, TARGET/d*100) / 100
    extra = max(0.0, need - total*p/100)
    print(f"  {k:<13} 真实 {d:5.1f}x  已下 {p:5.1f}%({d*p/100:4.1f}x)  需补 {extra:5.2f} GB")
