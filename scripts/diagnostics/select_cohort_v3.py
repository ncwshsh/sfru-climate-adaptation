# -*- coding: utf-8 -*-
"""正式队列 v3：深度分档 + 预算感知 + 每空间点精度评估。

v2 的教训
  AF 模块用「每单元 99 上限」→ 198 个高深度样本、1119 GB，却只有 8 个空间点。
  ANGSD 估计一个空间点的等位频率，25 个个体早已饱和，剩下 170 个样本纯浪费。

v3 的三条修正
  1) 每空间点样本数按深度分档：深度越低需要越多个体来补偿单个体的不确定度
       LOW  (d<12x)  → 12 个体/点
       MID  (12~28x) → 6  个体/点
       HIGH (>28x)   → 3  个体/点
     （可用模块覆盖，如 AF 强制 2/点当"地理锚点"）
  2) 成本仍按 nominal 上限 25x 截断：cost = 0.226 * min(depth, 25) GB
  3) 报「每点等位频率标准误」代理指标 SE≈sqrt(0.25/(2n))，n=该点个体数
     —— 一眼看出「30 个点各 1 个体」其实每个点都很虚
"""
import csv, os, collections, statistics, math

T = r"C:\SF_data\tools"
M = os.path.join(T, "sfru_wgs_matrix.tsv")
GPX = 5.65 / 25.0
BW = 2.4
TGT_NOM = 25.0

# code -> (study, 每单元上限 or "auto", 说明)
MODULES = {
    "BR": ("PRJNA545483", "auto", "巴西 30 市镇 · 44~144x · Illumina"),
    "US": ("PRJNA1115088", "auto", "美国 14 县 · 3~10x · Illumina"),
    "FL": ("PRJNA639296", "auto", "佛州 Citra/Jacksonville · 14~29x · Illumina"),
    "AM": ("PRJNA640063", "auto", "美洲 5 国 + 肯尼亚 · 36~76x · Illumina"),
    "AF": ("PRJNA591441", 2, "非洲 7 国 + 中国 · 34~423x · Illumina [锚点]"),
    "CN": ("PRJNA553264", 6, "中国 广东/云南 2 点 · 29~146x · BGISEQ"),
    "MY": ("PRJNA1061840", 6, "马来西亚 3 州 6 点 · DNBSEQ"),
    "ZJ": ("PRJNA590312", 3, "中国 浙江 1 点 · Illumina"),
    "SN": ("PRJNA1015028", 3, "塞内加尔 Casamance 1 点 · 上限 3"),
    "IN": ("PRJNA639295", 3, "印度/贝宁 4 点 · Illumina"),
}


def tier_cap(d):
    if d < 12:
        return 12
    if d < 28:
        return 6
    return 3


def unit_of(r):
    c = r.get("country") or "?"
    ct = c.split(":")[0].strip()
    sb = c.split(":", 1)[1].strip() if ":" in c else "(国)"
    return (ct, sb)


rows = list(csv.DictReader(open(M, encoding="utf-8"), delimiter="\t"))


def is_short(r):
    return "PACBIO" not in (r.get("platform") or "").upper() \
        and "NANOPORE" not in (r.get("platform") or "").upper()


mod_runs = {}
print("模块池与深度分档摘取")
print("-" * 108)
for code, (st, cap, desc) in MODULES.items():
    v = [r for r in rows if r["study"] == st and is_short(r)
         and (r.get("has_fastq") or "Y") == "Y"]
    byu = collections.defaultdict(list)
    for r in v:
        byu[unit_of(r)].append(r)
    sel = []
    for u, lst in byu.items():
        lst.sort(key=lambda x: -float(x["depth_x"] or 0))
        cap_u = tier_cap(float(lst[0]["depth_x"] or 0)) if cap == "auto" else cap
        sel += lst[:cap_u]
    mod_runs[code] = (sel, byu)
    d = [float(r["depth_x"] or 0) for r in sel]
    print(f"{code:<4}{st:<15}池{len(v):>4} 点{len(byu):>3} → 取{len(sel):>4}  "
          f"深度{min(d):>5.1f}~{max(d):<6.1f}中位{statistics.median(d):>5.1f}x  "
          f"{desc}")


def cost(sel):
    return sum(GPX * min(float(r["depth_x"] or 0), TGT_NOM) for r in sel)


def stat(sel):
    pts = collections.Counter(unit_of(r) for r in sel)
    p = len(pts)
    n = len(sel)
    mean_n = n / p if p else 0
    se = math.sqrt(0.25 / (2 * mean_n)) if mean_n else 0
    lo = min(pts.values()) if pts else 0
    hi = max(pts.values()) if pts else 0
    return n, p, cost(sel), mean_n, se, lo, hi


SCEN = {
    "S1 梯度主力（美+巴）": ["BR", "US"],
    "S2 主力+旧大陆锚点": ["BR", "US", "FL", "AM", "AF", "CN"],
    "S3 全范围": ["BR", "US", "FL", "AM", "AF", "CN", "MY", "ZJ", "SN", "IN"],
}

print("\n" + "=" * 108)
print("方案对比  （点/100GB = 空间点性价比；SE = 每空间点平均等位频率标准误代理）")
print("=" * 108)
hdr = f"{'方案':<22}{'样本':>6}{'空间点':>7}{'下载GB':>9}{'天':>6}{'点/100GB':>10}{'点均个体':>9}{'SE':>7}"
print(hdr)
print("-" * 108)
res = {}
for name, codes in SCEN.items():
    sel = [r for c in codes for r in mod_runs[c][0]]
    n, p, gb, mn, se, lo, hi = stat(sel)
    res[name] = (sel, gb, p)
    print(f"{name:<22}{n:>6}{p:>7}{gb:>9.0f}{gb*1024/BW/3600/24:>6.1f}"
          f"{p/(gb/100) if gb else 0:>10.1f}{mn:>9.1f}{se:>7.3f}")

print("\n对照：v2（每单元 99 上限）与旧深度池")
v2 = os.path.join(T, "cohort_v2.tsv")
if os.path.exists(v2):
    keys2 = {r["run"] for r in csv.DictReader(open(v2, encoding="utf-8"), delimiter="\t")}
    # v2 文件把行政区拆成两列、丢了原始 country 串 → 必须回矩阵重取 unit
    sel2 = [r for r in rows if r["run"] in keys2]
    n, p, gb, mn, se, lo2, hi2 = stat(sel2)
    print(f"{'v2 推荐(旧)':<22}{n:>6}{p:>7}{gb:>9.0f}{gb*1024/BW/3600/24:>6.1f}"
          f"{p/(gb/100) if gb else 0:>10.1f}{mn:>9.1f}{se:>7.3f}")

print("\n" + "=" * 108)
print("S2 主力+旧大陆锚点：模块明细")
print("=" * 108)
for code in SCEN["S2 主力+旧大陆锚点"]:
    sel, byu = mod_runs[code]
    n, p, gb, mn, se, lo, hi = stat(sel)
    print(f"  {code:<4}{MODULES[code][0]:<15}n={n:<4}点={p:<3} {gb:>7.1f}GB "
          f"{gb/p if p else 0:>6.1f}GB/点  点内个体{lo}~{hi}(均{mn:.1f})  SE={se:.3f}  {MODULES[code][2]}")

out = os.path.join(T, "cohort_v3.tsv")
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["run", "study", "module", "country", "subnational", "platform",
                "depth_x", "target_nominal_x", "dl_GB"])
    for code in SCEN["S2 主力+旧大陆锚点"]:
        for r in sorted(mod_runs[code][0], key=lambda x: (x["study"], x["country"], x["run"])):
            u = unit_of(r)
            w.writerow([r["run"], r["study"], code, u[0], u[1], r["platform"],
                        r["depth_x"], f"{min(float(r['depth_x'] or 0), TGT_NOM):.1f}",
                        f"{GPX*min(float(r['depth_x'] or 0), TGT_NOM):.2f}"])
print(f"\n[写出] {out}")
