# -*- coding: utf-8 -*-
"""S2 正式队列 · 定案 B（等深度化 T=6x / 下限 F=5x）采购清单生成。

胡博士 2026-09-17 定案：
  主线 = 个体级 GEA；为消除「深度 ↔ 地区」混淆，统一下载目标 T=6x 名义（≈3.6x 可用），
  深度下限 F=5x（保住美国 14 县全覆盖）。所有样本在 BAM 层降采样对齐到 T。

PCT 规则：depth <= T -> 100%；depth > T -> ceil(T/depth*100)
⚠️ 改百分比 = 整份重下（dl_ena.sh 块名含 PCT）=> PCT 必须一次定对。

复用判定（★ T 降到 6x 的红利）：
  磁盘已有残片，若「磁盘名义深度 >= T」且「双端齐全」且「已成文件（非未拼接块）」
  -> 直接复用，不再下载。
"""
import csv, os, re, glob, collections, math

T = r"C:\SF_data\tools"
RAW = r"C:\SF_data\01_raw"
SRC = os.path.join(T, "cohort_v3.tsv")
FORMAL = os.path.join(T, "cohort_formal_s2.tsv")
MAN = os.path.join(T, "dl_manifest_s2.tsv")
OUTDIR = "C:/SF_data/01_raw"
GPX = 5.65 / 25.0
BW = 2.4
TGT = 6.0      # ★ 统一下载目标（名义）
FLOOR = 5.0    # ★ 深度下限

# ---------- 1. 读队列 ----------
rows = list(csv.DictReader(open(SRC, encoding="utf-8"), delimiter="\t"))
print(f"读入 S2 队列 {len(rows)} 个 run")

# ---------- 2. 深度下限过滤 ----------
drop = [r for r in rows if float(r["depth_x"]) < FLOOR]
rows = [r for r in rows if float(r["depth_x"]) >= FLOOR]
for m in sorted({r["module"] for r in drop}):
    sub = [r for r in drop if r["module"] == m]
    print(f"  剔除（深度<{FLOOR}x） {m}: {len(sub)} 个  "
          f"深度 {min(float(x['depth_x']) for x in sub):.1f}~"
          f"{max(float(x['depth_x']) for x in sub):.1f}x")
print(f"下限过滤后 {len(rows)} 个")

# ---------- 3. 复用判定 ----------
# ⚠️ 字节数只能统计「已成文件」（_1/_2 .fastq.gz[.partialN]），
#    不能把未拼接的 .partN 块算进去（否则会虚高、把残块误判成可用）
done = collections.defaultdict(set)
disk_gb = collections.defaultdict(float)
for p in glob.glob(os.path.join(RAW, "*")):
    m = re.match(r"(SRR\d+)_([12])\.fastq\.gz(\.partial\d+)?$", os.path.basename(p))
    if m and os.path.isfile(p):
        done[m.group(1)].add(m.group(2))
        disk_gb[m.group(1)] += os.path.getsize(p) / 1e9

reuse = []
for r in rows:
    run = r["run"]
    if len(done.get(run, set())) < 2:
        continue
    if disk_gb[run] / GPX >= TGT:
        reuse.append(run)
print(f"可复用 {len(reuse)} 个（磁盘已成文件深度 >= {TGT}x 且双端齐全）")
for x in sorted(reuse):
    print(f"    {x}  {disk_gb[x]:.2f} GB = {disk_gb[x]/GPX:.1f}x")

# ---------- 4. 目标与 PCT ----------
for r in rows:
    d = float(r["depth_x"])
    tn = min(d, TGT)
    r["_pct"] = 100 if d <= TGT else math.ceil(TGT / d * 100)
    r["_reuse"] = r["run"] in reuse
    r["target_nominal_x"] = f"{tn:.1f}"
    r["dl_GB"] = "0.00" if r["_reuse"] else f"{GPX*tn:.2f}"
    r["_gb"] = 0.0 if r["_reuse"] else GPX * tn

# ---------- 5. 写出正式队列 ----------
with open(FORMAL, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["run", "study", "module", "country", "subnational", "platform",
                "depth_x", "target_nominal_x", "pct", "dl_GB", "reuse_local"])
    for r in sorted(rows, key=lambda x: (x["module"], x["study"], x["run"])):
        w.writerow([r["run"], r["study"], r["module"], r["country"], r["subnational"],
                    r["platform"], r["depth_x"], r["target_nominal_x"],
                    r["_pct"], r["dl_GB"], "Y" if r["_reuse"] else ""])
print(f"[写出] {FORMAL}  {len(rows)} 行")

# ---------- 6. 采购清单 ----------
with open(MAN, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["run", "study", "module", "depth_x", "target_nominal_x", "pct", "dl_GB"])
    for r in sorted(rows, key=lambda x: (x["module"], x["run"])):
        if r["_reuse"]:
            continue
        w.writerow([r["run"], r["study"], r["module"], r["depth_x"],
                    r["target_nominal_x"], r["_pct"], r["dl_GB"]])
print(f"[写出] {MAN}")

# ---------- 7. 模块汇总 ----------
mod = collections.defaultdict(lambda: {"n": 0, "gb": 0.0, "re": 0, "ds": [],
                                       "study": "", "pct100": 0})
for r in rows:
    m = mod[r["module"]]
    m["n"] += 1
    m["gb"] += r["_gb"]
    m["re"] += 1 if r["_reuse"] else 0
    m["ds"].append(float(r["depth_x"]))
    m["study"] = r["study"]
    m["pct100"] += 1 if r["_pct"] == 100 else 0

tot = sum(m["gb"] for m in mod.values())
print("\n" + "=" * 96)
print(f"S2 定案 B（统一 {TGT:.0f}x 名义 / 下限 {FLOOR:.0f}x）· 采购清单")
print("=" * 96)
print(f"{'模块':<5}{'study':<15}{'样本':>5}{'复用':>5}{'下满/部分':>10}{'深度范围':>16}{'下载GB':>9}{'占比':>7}")
print("-" * 96)
for code in sorted(mod, key=lambda c: -mod[c]["gb"]):
    m = mod[code]
    print(f"{code:<5}{m['study']:<15}{m['n']:>5}{m['re']:>5}"
          f"{str(m['n']-m['re']-m['pct100'])+'/'+str(m['pct100']):>10}"
          f"{min(m['ds']):>7.1f}~{max(m['ds']):<8.1f}{m['gb']:>9.1f}{m['gb']/tot*100:>6.1f}%")
print("-" * 96)
print(f"{'合计':<20}{len(rows):>5}{len(reuse):>5}{'':>10}{'':>16}{tot:>9.1f}")
print(f"实际待下 {len(rows)-len(reuse)} 个 / {tot:.1f} GB / {tot*1024/BW/3600:.1f} h = "
      f"{tot*1024/BW/3600/24:.1f} 天（带宽 {BW} MB/s）")

# ---------- 8. 批量脚本 ----------
os.makedirs(os.path.join(T, "dl_s2"), exist_ok=True)
for code in sorted(mod):
    sel = [r for r in rows if r["module"] == code and not r["_reuse"]]
    p = os.path.join(T, "dl_s2", f"dl_{code}.sh")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("#!/usr/bin/env bash\n")
        f.write(f"# 模块 {code} | {mod[code]['study']} | 待下 {len(sel)} 个 "
                f"(复用 {mod[code]['re']}) | {mod[code]['gb']:.1f} GB\n")
        f.write('export PATH="/usr/bin:/bin:$PATH"\n')
        f.write('cd "$(dirname "$0")/.." || exit 1\n')
        f.write('OUTDIR="C:/SF_data/01_raw"\n')
        if not sel:
            f.write('echo "本模块全部复用本地文件，无需下载"\nexit 0\n')
        else:
            f.write('for spec in \\\n')
            for r in sel:
                f.write(f'  "{r["run"]} {r["_pct"]}" \\\n')
            f.write("; do\n")
            f.write('  set -- $spec\n')
            f.write('  echo "=== $1  PCT=$2  $(date +%H:%M:%S) ==="\n')
            f.write('  bash dl_ena.sh "$1" 8 16 "$OUTDIR" "$2"\n')
            f.write("done\n")
    print(f"[写出] dl_s2/dl_{code}.sh  ({len(sel)} 个待下)")

p = os.path.join(T, "dl_s2", "dl_all.sh")
with open(p, "w", encoding="utf-8", newline="\n") as f:
    f.write("#!/usr/bin/env bash\n# S2 定案 B 总下载入口\nset -u\n")
    for code in sorted(mod, key=lambda c: -mod[c]["gb"]):
        f.write(f'echo "########## {code} ({mod[code]["gb"]:.1f} GB) ##########"\n')
        f.write(f'bash "$(dirname "$0")/dl_{code}.sh"\n')
print(f"[写出] dl_s2/dl_all.sh")

with open(os.path.join(T, "reuse_s2.txt"), "w", encoding="utf-8") as f:
    for r in sorted(reuse):
        f.write(f"{r}\t{disk_gb[r]:.2f}GB\t{disk_gb[r]/GPX:.1f}x\n")
print(f"[写出] reuse_s2.txt  ({len(reuse)} 个)")
