# -*- coding: utf-8 -*-
"""深度混淆诊断 + 等深度化方案预算核算。

背景：个体级 GEA（RDA/LFMM2/BayPass）中，个体基因型的不确定度随深度变化，
      低深度个体的剂量被压向群体均值。若深度沿地理/气候梯度变化（本队列正是如此：
      US 3.5x ←→ BR 38.9x），就会伪造出一条梯度信号。

解决办法：把「目标深度」从 min(深度,25x) 改成 **全局统一值 T**，并在 BAM 层降采样对齐。
      降采样免费（已有数据），且因为要统一下载目标，还能省大量带宽。
"""
import csv, collections, statistics

T = r"C:\SF_data\tools"
GPX = 5.65 / 25.0
BW = 2.4
rows = list(csv.DictReader(open(T + r"\cohort_formal_s2.tsv", encoding="utf-8"),
                           delimiter="\t"))
MODS = ["US", "BR", "AF", "AM", "CN", "FL"]


def scen(target, floor=0.0):
    """target=统一目标名义深度；floor=深度下限（低于则剔除）"""
    keep, gb = [], 0.0
    for r in rows:
        d = float(r["depth_x"])
        if d < floor:
            continue
        keep.append(r)
        gb += GPX * min(d, target)
    return keep, gb


def depth_spread(sel, target):
    ds = [min(float(r["depth_x"]), target) for r in sel]
    return min(ds), max(ds), max(ds) / min(ds)


print("=" * 100)
print("方案对比：统一目标深度 vs 当前 S2")
print("=" * 100)
print(f"{'方案':<34}{'样本':>6}{'GB':>8}{'天':>6}{'深度范围(名义)':>20}{'极差':>7}{'可用中位':>9}")
print("-" * 100)


def line(name, sel, gb, target):
    ds = [min(float(r["depth_x"]), target) for r in sel]
    med = statistics.median(ds) * 0.6
    print(f"{name:<34}{len(sel):>6}{gb:>8.0f}{gb*1024/BW/3600/24:>6.1f}"
          f"{f'{min(ds):.1f}~{max(ds):.1f}x':>20}{max(ds)/min(ds):>7.1f}{med:>8.1f}x")


sel0 = rows
gb0 = sum(GPX * min(float(r["depth_x"]), 25.0) for r in rows)
line("当前 S2（目标 min(d,25x)）", sel0, gb0, 25.0)

for tg in (4.0, 5.0, 6.0):
    sel, gb = scen(tg)
    line(f"统一 {tg:.0f}x（保留全部）", sel, gb, tg)
for tg, fl in ((5.0, 4.0), (6.0, 5.0), (8.0, 6.0)):
    sel, gb = scen(tg, fl)
    line(f"统一 {tg:.0f}x + 下限 {fl:.0f}x", sel, gb, tg)

print("\n" + "=" * 100)
print("推荐方案「统一 5x 名义（≈3x 可用）」逐模块")
print("=" * 100)
sel, gb = scen(5.0)
print(f"{'模块':<5}{'样本':>5}{'GB':>8}{'原 S2 GB':>10}{'省下':>8}{'深度范围':>16}{'等深度化后':>12}")
print("-" * 80)
for m in MODS:
    sub = [r for r in rows if r["module"] == m]
    s2gb = sum(GPX * min(float(r["depth_x"]), 25.0) for r in sub)
    g = sum(GPX * min(float(r["depth_x"]), 5.0) for r in sub)
    ds = [min(float(r["depth_x"]), 5.0) for r in sub]
    print(f"{m:<5}{len(sub):>5}{g:>8.1f}{s2gb:>10.1f}{s2gb-g:>8.1f}"
          f"{f'{min(ds):.1f}~{max(ds):.1f}x':>16}{'全部 5.0x' if min(ds)>=5 else '含更浅':>12}")
print("-" * 80)
print(f"合计 {len(sel)} 样本 / {gb:.0f} GB（原 {gb0:.0f} GB，省 {gb0-gb:.0f} GB = {(gb0-gb)/gb0*100:.0f}%）")
print(f"耗时 {gb*1024/BW/3600/24:.1f} 天（原 {gb0*1024/BW/3600/24:.1f} 天）")

print("\n⚠️ 但统一下载目标会带来一个不可逆的代价：")
print("   高深度样本被截到 5x 后，将来若想提高深度，必须整份重下（PCT 变了）。")
print("   折中做法：仍按 5x 下载（省资源），但**先把 5x 版本跑通全流程**，")
print("   确认能出信号后再决定是否补下高深度样本做敏感性分析。")
