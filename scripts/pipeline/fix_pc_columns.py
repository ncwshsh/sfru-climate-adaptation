# -*- coding: utf-8 -*-
"""把 pca_scores.tsv 的 PC1–PC4 补进 gea_input.tsv / gea_input_P.tsv。

背景（2026-10-03）：这两张表的 PC1–PC4 列一直是**空的**，导致
  * Fig2 完全画不出点（标题还显示 r = +nan）
  * check_corr_scope.py 算 PC 相关相关系数得到 nan
真正的 PC 数据在 /home/hugo/data/angsd/pca_scores.tsv（分析脚本 gea_rda/gea_lfmm
一直直接读它，所以论文的 R² 与 PC 相关系数不受影响）。

做法：只替换 PC1–PC4 这几列的文本，**其余列原样写回**（不重排、不改格式）。
"""
import csv, io, os, shutil, sys

REPORT = "/mnt/c/SF_data/tools/report"
PCA = "/home/hugo/data/angsd/pca_scores.tsv"
TARGETS = ["gea_input.tsv", "gea_input_P.tsv"]
PCOLS = ["PC1", "PC2", "PC3", "PC4"]

# 读 PC 分数
pcs = {}
with io.open(PCA, encoding="utf-8") as fh:
    for r in csv.DictReader(fh, delimiter="\t"):
        pcs[r["run"]] = r
print("pca_scores.tsv: %d runs" % len(pcs))

for name in TARGETS:
    path = os.path.join(REPORT, name)
    bak = path + ".bak_nopc"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with io.open(path, encoding="utf-8") as fh:
        rd = csv.DictReader(fh, delimiter="\t")
        cols = rd.fieldnames
        rows = list(rd)
    miss = [r["run"] for r in rows if r["run"] not in pcs]
    filled = 0
    for r in rows:
        p = pcs.get(r["run"])
        if not p:
            continue
        for c in PCOLS:
            if c in r:
                r[c] = p[c]
                filled += 1
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t",
                           lineterminator="\n", restval="")
        w.writeheader()
        w.writerows(rows)
    print("%-18s rows=%d  filled=%d  对不上的 run=%d %s"
          % (name, len(rows), filled, len(miss), miss[:5]))

# 复核
print("\n=== 复核 ===")
for name in TARGETS:
    with io.open(os.path.join(REPORT, name), encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    print(name)
    for c in PCOLS:
        ne = sum(1 for r in rows if r[c] not in ("", "NA", "nan"))
        print("   %-4s 非空 %3d/%d" % (c, ne, len(rows)))
    # 确认其他列没被动
    print("   run/module/lat 首行:", rows[0]["run"], rows[0]["module"], rows[0]["lat"])
