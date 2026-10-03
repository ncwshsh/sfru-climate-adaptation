# -*- coding: utf-8 -*-
"""pca_summarize.py —— 把 PCAngsd 的协方差矩阵变成结构图 + 混淆诊断的第二块证据

输入：
  /home/hugo/data/angsd/pca_s2.cov   （PCAngsd 产出，214×214）
  /mnt/c/SF_data/tools/bamlist_keep214.txt  （样本顺序，必须与协方差矩阵一致）
  /mnt/c/SF_data/tools/report/qc_s2_bm2k15.tsv （模块/国家/纬度/比对率/深度）

产出：
  /home/hugo/data/angsd/pca_scores.tsv
  /mnt/c/SF_data/tools/report/pca_s2_PC1PC2.png
  /mnt/c/SF_data/tools/report/pca_s2_PC1_lat_US.png
"""
import numpy as np
import os

COV = "/home/hugo/data/angsd/pca_s2.cov"
BAMLIST = "/mnt/c/SF_data/tools/bamlist_keep214.txt"
QC = "/mnt/c/SF_data/tools/report/qc_s2_bm2k15.tsv"
OUTTSV = "/home/hugo/data/angsd/pca_scores.tsv"
OUTDIR = "/mnt/c/SF_data/tools/report"
os.makedirs(OUTDIR, exist_ok=True)

# ---- 样本顺序 ----
runs = [os.path.basename(l.strip()).split(".")[0]
        for l in open(BAMLIST) if l.strip()]

# ---- 元数据 ----
meta = {}
with open(QC, encoding="utf-8") as fh:
    hdr = fh.readline().rstrip("\n").split("\t")
    for line in fh:
        p = line.rstrip("\n").split("\t")
        d = dict(zip(hdr, p))
        meta[d["run"]] = d

# ---- 协方差 → 特征分解 ----
C = np.loadtxt(COV)
n = C.shape[0]
assert n == len(runs), "协方差矩阵维度 %d 与样本数 %d 不符" % (n, len(runs))
w, v = np.linalg.eigh(C)
order = np.argsort(w)[::-1]
w = w[order]
v = v[:, order]
pcs = v * np.sqrt(np.maximum(w, 0))      # 个体坐标
vexp = 100 * w / w.sum()

print("样本数: %d" % n)
print("前 10 个主成分解释方差 (%):")
print("  " + "  ".join("PC%d=%.2f" % (i + 1, vexp[i]) for i in range(min(10, len(vexp)))))

with open(OUTTSV, "w", encoding="utf-8") as fh:
    fh.write("run\tmodule\tcountry\tlat\t" + "\t".join("PC%d" % (i + 1) for i in range(6))
             + "\trate\traw_depth\n")
    for i, r in enumerate(runs):
        m = meta.get(r, {})
        fh.write("\t".join([r, m.get("module", "?"), m.get("country", "?"), m.get("lat", ""),
                            "\t".join("%.6f" % pcs[i, k] for k in range(6)),
                            m.get("rate", ""), m.get("raw_depth", "")]) + "\n")
print("已写出: %s" % OUTTSV)

# ---- 混淆诊断第二部分：PC 与纬度 / 比对率 / 深度 的相关 ----
def pearson(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ok = ~(np.isnan(a) | np.isnan(b))
    a, b = a[ok], b[ok]
    if len(a) < 5:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])

mods = np.array([meta.get(r, {}).get("module", "?") for r in runs])
lats = np.array([float(meta.get(r, {}).get("lat")) if meta.get(r, {}).get("lat") not in (None, "") else np.nan for r in runs])
rates = np.array([float(meta.get(r, {}).get("rate", np.nan)) for r in runs])
deps = np.array([float(meta.get(r, {}).get("raw_depth", np.nan)) for r in runs])

print()
print("=== PC1~PC4 与技术/地理协变量的相关（全队列）===")
for k in range(4):
    print("  PC%d  纬度 r=%+.3f   比对率 r=%+.3f   深度 r=%+.3f"
          % (k + 1, pearson(pcs[:, k], lats), pearson(pcs[:, k], rates), pearson(pcs[:, k], deps)))

print()
print("=== 美国模块内部（气候梯度的主战场）===")
sel = mods == "US"
for k in range(4):
    print("  PC%d  纬度 r=%+.3f   比对率 r=%+.3f   深度 r=%+.3f"
          % (k + 1,
             pearson(pcs[sel, k], lats[sel]),
             pearson(pcs[sel, k], rates[sel]),
             pearson(pcs[sel, k], deps[sel])))

# ---- 画图 ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

colors = {"US": "#c0392b", "BR": "#2980b9", "AF": "#27ae60",
          "AM": "#8e44ad", "CN": "#f39c12", "FL": "#16a085"}
fig, ax = plt.subplots(1, 2, figsize=(13, 5.5))
for m in ["US", "BR", "AF", "AM", "CN", "FL"]:
    s = mods == m
    if s.sum() == 0:
        continue
    ax[0].scatter(pcs[s, 0], pcs[s, 1], s=26, alpha=.75, label="%s (%d)" % (m, s.sum()),
                  c=colors.get(m, "#666666"), edgecolors="none")
ax[0].set_xlabel("PC1 (%.2f%%)" % vexp[0])
ax[0].set_ylabel("PC2 (%.2f%%)" % vexp[1])
ax[0].legend(fontsize=9, markerscale=1.4)
ax[0].set_title("PCAngsd: PC1 vs PC2 (214 samples, ~1.01M sites)", fontsize=11)
ax[0].axhline(0, color="#cccccc", lw=.7)
ax[0].axvline(0, color="#cccccc", lw=.7)

# 美国内部：PC1 vs 纬度
us = mods == "US"
sc = ax[1].scatter(lats[us], pcs[us, 0], s=30, alpha=.8, c=rates[us], cmap="viridis", edgecolors="none")
ax[1].set_xlabel("Latitude (US samples)")
ax[1].set_ylabel("PC1")
ax[1].set_title("US: PC1 vs Latitude (color = mapping rate %)", fontsize=11)
plt.colorbar(sc, ax=ax[1], label="mapping rate %")
r = pearson(pcs[us, 0], lats[us])
ax[1].text(0.03, 0.95, "r = %+.3f" % r, transform=ax[1].transAxes, fontsize=11,
           va="top", bbox=dict(fc="white", ec="#999999"))

plt.tight_layout()
p1 = os.path.join(OUTDIR, "pca_s2_PC1PC2.png")
plt.savefig(p1, dpi=140)
print()
print("已写出: %s" % p1)
