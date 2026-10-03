# -*- coding: utf-8 -*-
"""正式队列选择：按「气候变异是否能在 study 内部独立变化」分模块。

设计原理（2026-09-17 建立）：
  本项目池子里 **study ≈ 国家**，国家间比较与测序批次完全混淆。
  因此气候效应只能靠 **study 内部的气候变异** 来识别（study 内批次恒定，气候自由变化）。
  故队列必须以「自身跨多国 或 跨多个空间单元」的 study 为骨架。
  ⇒ 用混合模型（study 作随机截距）时，气候效应由组内变异估计，不被批次污染。

空间单元定义 = (study, 国家, 次级地名)。
  注意：无次级地名时，单元就是**国家**本身 —— 跨多国的 study 每个国家各算一个单元。
"""
import csv, os, collections

T = r"C:\SF_data\tools"
GPX = 5.65 / 25.0
BW = 2.4
TGT_NOM = 25.0          # 名义目标（usable ~15x）

rows = [r for r in csv.DictReader(
    open(os.path.join(T, "cohort_pool_1215x.tsv"), encoding="utf-8"), delimiter="\t")]


def ctry(r):
    return (r["country"] or "?").split(":")[0].strip()


def sub(r):
    return r["country"].split(":", 1)[1].strip() if ":" in r["country"] else "(无)"


def unit_of(r):
    return (r["study"], ctry(r), sub(r))


MODULES = {
    "PRJNA545483": ("M1 巴西国内梯度", "30 个市镇 · 纬度跨 ~28°", 3),
    "PRJNA640063": ("M2 美洲跨国内梯度", "5 国 · 纬度跨 ~70°", 3),
    "PRJNA591441": ("M3 非洲跨国内梯度", "7 国 · 含中国", 3),
    "PRJNA553264": ("M4 中国华南", "广东 14 + 云南 4 · BGISEQ", 2),
    "PRJNA590312": ("M5 中国浙江", "浙江 2 · Illumina", 1),
    "PRJNA1061840": ("M6 马来西亚", "3 个相邻州（气候变异弱）· DNBSEQ", 1),
    "PRJNA639295": ("M7 印度/贝宁", "各 2 · 无次级地名", 1),
    "PRJNA1015028": ("M8 塞内加尔", "Casamance 单一地点（无梯度）", 0),
}

by = collections.defaultdict(list)
for r in rows:
    by[r["study"]].append(r)

print("=" * 104)
print("模块清单（按组内气候变异潜力排序）")
print("=" * 104)
for st, (name, desc, tier) in sorted(MODULES.items(), key=lambda x: -x[1][2]):
    v = by.get(st, [])
    if not v:
        print(f"  {name:<22}{st:<15} 池中无样本")
        continue
    units = collections.Counter(unit_of(x) for x in v)
    plats = collections.Counter(x["platform"] for x in v)
    mark = "★" * tier if tier else "☆"
    print(f"  {mark} {name:<22}{st:<15} n={len(v):<4}空间单元={len(units):<3} 平台={dict(plats)}")
    print(f"      └ {desc}")


def build(mods):
    sel = [r for r in rows if r["study"] in mods]
    n = len(sel)
    gb = n * GPX * TGT_NOM
    units = len({unit_of(r) for r in sel})
    plats = collections.Counter(r["platform"] for r in sel)
    return sel, n, gb, units, plats


SCEN = {
    "A 核心梯度": ["PRJNA545483", "PRJNA640063", "PRJNA591441"],
    "B 核心+亚洲（推荐）": ["PRJNA545483", "PRJNA640063", "PRJNA591441",
                     "PRJNA553264", "PRJNA590312"],
    "C A+亚洲+马来": ["PRJNA545483", "PRJNA640063", "PRJNA591441",
                  "PRJNA553264", "PRJNA590312", "PRJNA1061840"],
    "D 全合格池": list(MODULES.keys()),
}

print("\n" + "=" * 104)
print("方案对比")
print("=" * 104)
print(f"{'方案':<22}{'样本':>6}{'空间单元':>9}{'下载GB':>9}{'时长h':>8}{'天':>6}  平台构成")
print("-" * 104)
res = {}
for name, mods in SCEN.items():
    sel, n, gb, units, plats = build(mods)
    res[name] = (sel, n, gb, units, plats)
    print(f"{name:<22}{n:>6}{units:>9}{gb:>9.0f}{gb*1024/BW/3600:>8.0f}"
          f"{gb*1024/BW/3600/24:>6.1f}  {dict(plats)}")

print("\n" + "=" * 104)
print("推荐方案 B 明细（按 区域/国家 × 空间单元）")
print("=" * 104)
sel, n, gb, units, plats = res["B 核心+亚洲（推荐）"]
byc = collections.defaultdict(list)
for r in sel:
    byc[(r["region"], ctry(r))].append(r)
for (reg, ct), v in sorted(byc.items()):
    print(f"  {reg:<20}{ct:<12}{len(v):>3} 样本  "
          f"{len({unit_of(x) for x in v}):>2} 单元  {dict(collections.Counter(x['platform'] for x in v))}")

out = os.path.join(T, "cohort_final_B.tsv")
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["run", "study", "module", "region", "country", "subnational",
                "platform", "depth_true_x", "target_nominal_x", "dl_GB", "patch"])
    for r in sorted(sel, key=lambda x: (x["study"], x["country"], x["run"])):
        name, desc, tier = MODULES[r["study"]]
        w.writerow([r["run"], r["study"], name, r["region"], r["country"], sub(r),
                    r["platform"], r["depth_true_x"], f"{TGT_NOM:.0f}",
                    f"{GPX*TGT_NOM:.2f}", 1 if r["platform"] == "ILLUMINA" else 2])
print(f"\n[写出] {out}  {len(sel)} 行")
