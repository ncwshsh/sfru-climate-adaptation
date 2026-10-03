# -*- coding: utf-8 -*-
"""正式队列选择 v2：以「空间点」为第一约束，纳入低深度高分辨率模块。

设计原理
  1) 池子里 study ≈ 国家 → 国家间比较与批次混淆 ⇒ 气候效应只能靠 **study 内部**的变异识别
  2) 气候关联统计的**有效样本量 = 独立空间点**，不是样本数
     ⇒ 优先选「单一 study 内部含多个分离空间点」的数据体
  3) 低深度样本**每个空间点更便宜**：成本 = 0.226 x min(深度, 25) GB
     ⇒ 5.4x 的样本只要 1.22 GB，而 57x 的要 5.65 GB；空间点的"单价"差 4.6 倍

模块来源一律为野外种群 study（已剔除细胞系/实验室株/感染实验）。
"""
import csv, os, collections, statistics

T = r"C:\SF_data\tools"
M = os.path.join(T, "sfru_wgs_matrix.tsv")
GPX = 5.65 / 25.0
BW = 2.4
TGT_NOM = 25.0

# 模块: code -> (study, 平台白名单, 每单元上限, 说明)
MODULES = {
    "BR": ("PRJNA545483", None, 99, "巴西 30 市镇 · 44~144x · Illumina"),
    "US": ("PRJNA1115088", None, 10, "美国 14 县 · 3~10x · Illumina ←空间点最多且最便宜"),
    "FL": ("PRJNA639296", None, 99, "佛州 Citra/Jacksonville · 14~29x · Illumina"),
    "AM": ("PRJNA640063", None, 99, "美洲 5 国 + 肯尼亚 · 36~76x · Illumina"),
    "AF": ("PRJNA591441", None, 99, "非洲 7 国 + 中国 · 34~423x · Illumina"),
    "CN": ("PRJNA553264", None, 99, "中国 广东14/云南4 · BGISEQ"),
    "MY": ("PRJNA1061840", None, 99, "马来西亚 3 州 · DNBSEQ"),
    "ZJ": ("PRJNA590312", None, 99, "中国 浙江 2 · Illumina"),
    "SN": ("PRJNA1015028", None, 12, "塞内加尔 Casamance（单点）· 上限 12"),
    "IN": ("PRJNA639295", None, 99, "印度/贝宁 各 2 · Illumina"),
}

rows = list(csv.DictReader(open(M, encoding="utf-8"), delimiter="\t"))


def plat(r):
    return (r.get("platform") or "").upper()


def is_short(r):
    return "PACBIO" not in plat(r) and "NANOPORE" not in plat(r)


def unit_of(r):
    ct = (r.get("country") or "?").split(":")[0].strip()
    sb = r["country"].split(":", 1)[1].strip() if ":" in (r.get("country") or "") else "(国)"
    return (ct, sb)


mod_runs = {}
for code, (st, _, cap, desc) in MODULES.items():
    v = [r for r in rows if r["study"] == st and is_short(r) and (r.get("has_fastq") or "Y") == "Y"]
    byu = collections.defaultdict(list)
    for r in v:
        byu[unit_of(r)].append(r)
    sel = []
    for u, lst in byu.items():
        lst.sort(key=lambda x: -float(x["depth_x"] or 0))
        sel += lst[:cap]
    mod_runs[code] = sel
    print(f"{code:<4}{st:<15} 池中 {len(v):>4} → 取 {len(sel):>4}  空间点 {len(byu):>3}  {desc}")


def cost(sel):
    return sum(GPX * min(float(r["depth_x"] or 0), TGT_NOM) for r in sel)


def pts(sel):
    return len({(r["study"], unit_of(r)) for r in sel})


SCEN = {
    "V1 双核心（美+巴）": ["BR", "US"],
    "V2 推荐": ["BR", "US", "FL", "AM", "AF", "CN"],
    "V3 扩展": ["BR", "US", "FL", "AM", "AF", "CN", "MY", "ZJ", "SN", "IN"],
}

print("\n" + "=" * 100)
print("方案对比（以空间点为核心指标）")
print("=" * 100)
print(f"{'方案':<22}{'样本':>6}{'空间点':>8}{'下载GB':>9}{'天':>6}   点/100GB")
print("-" * 100)
res = {}
for name, codes in SCEN.items():
    sel = [r for c in codes for r in mod_runs[c]]
    gb = cost(sel)
    p = pts(sel)
    res[name] = (sel, gb, p)
    print(f"{name:<22}{len(sel):>6}{p:>8}{gb:>9.0f}{gb*1024/BW/3600/24:>6.1f}"
          f"{p/ (gb/100) if gb else 0:>13.1f}")

print("\n对照：旧方案（只看深度，未纳入低深度模块）")
old = [r for r in csv.DictReader(open(os.path.join(T, "cohort_pool_1215x.tsv"),
                                      encoding="utf-8"), delimiter="\t")]
for nm, mods in [("A 核心梯度", ["PRJNA545483", "PRJNA640063", "PRJNA591441"]),
                 ("B 核心+亚洲", ["PRJNA545483", "PRJNA640063", "PRJNA591441",
                              "PRJNA553264", "PRJNA590312"]),
                 ("D 全合格池", None)]:
    sel = [r for r in old if mods is None or r["study"] in mods]
    gp = len({(r["study"], (r["country"] or "?").split(":")[0]) for r in sel})
    gb = len(sel) * GPX * TGT_NOM
    print(f"  {nm:<22}{len(sel):>6}{gp:>8}{gb:>9.0f}{gb*1024/BW/3600/24:>6.1f}"
          f"{gp/(gb/100):>13.1f}")

print("\n" + "=" * 100)
print("V2 推荐方案：模块明细")
print("=" * 100)
sel, gb, p = res["V2 推荐"]
for code in SCEN["V2 推荐"]:
    v = mod_runs[code]
    st = MODULES[code][0]
    d = [float(r["depth_x"] or 0) for r in v]
    print(f"  {code:<4}{st:<15} n={len(v):<4}点={pts(v):<3}"
          f"深度 {min(d):>5.1f}~{max(d):<6.1f}中位 {statistics.median(d):>6.1f}x  "
          f"{cost(v):>6.1f} GB  {MODULES[code][3]}")

out = os.path.join(T, "cohort_v2.tsv")
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["run", "study", "module", "country", "subnational", "platform",
                "depth_x", "target_nominal_x", "dl_GB"])
    for code in SCEN["V2 推荐"]:
        for r in sorted(mod_runs[code], key=lambda x: (x["study"], x["country"], x["run"])):
            u = unit_of(r)
            w.writerow([r["run"], r["study"], code, u[0], u[1], r["platform"],
                        r["depth_x"], f"{min(float(r['depth_x'] or 0), TGT_NOM):.1f}",
                        f"{GPX*min(float(r['depth_x'] or 0), TGT_NOM):.2f}"])
print(f"\n[写出] {out}  {len(sel)} 行")
