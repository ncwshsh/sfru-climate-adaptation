# -*- coding: utf-8 -*-
"""crossregion_genes.py —— 同口径跨国比较：各地区按自己的气候轴选候选，再比基因集重合

与上一版的区别（这是关键）：
  上一版是用**美国**的 top 位点去别的地区里量，天然吃亏——各地气候轴的方向和变量都不同。
  这一版让**每个地区按自己的主气候轴**各自选 top 1% 位点，再比最终的**基因集**，
  属于同口径比较。

窗口说明：候选位点映射到基因用 **±2 kb**。
  若用 ±20 kb，10145 个位点会覆盖约 400 Mb ≈ 整个基因组，基因集没有区分度（等于全选）。

统计检验：两两基因集重叠用**超几何检验**（背景 = 全部 16769 个基因）。
"""
import os
import re
import gzip
import numpy as np
import pandas as pd
from scipy.stats import hypergeom

ROOT = "/mnt/c/SF_data"
GFF = os.path.join(ROOT, "00_ref", "GCF_023101765.2_genomic.gff.gz")
REP = os.path.join(ROOT, "tools", "report")
GROUPS = ["US-C", "BR-C", "AF-C", "AM-C", "CN-C"]
# ★ 敏感性分析支持（2026-09-24）：设 SUFFIX=_excl3 即读写带后缀的 z / 结果文件，不覆盖原结果
SUFFIX = os.environ.get("SUFFIX", "")
WIN = 2000
TOPF = 0.002       # 各取 |z| 前 0.2%
# ⚠️ 第一版用 top 1%（10145 个位点）→ 映射到 4000~5000 个基因 = 基因组 30%，
#    完全没有区分度（三个功能模块的富集值一模一样就是这个症状）。
#    位点太多时 ±2kb 窗口把整个基因组都覆盖了。改用 top 0.2%（约 2000 位点）。
OUTG = os.path.join(REP, "crossregion_genes%s.tsv" % SUFFIX)
OUTP = os.path.join(REP, "crossregion_genes%s.png" % SUFFIX)

MODULES = {
    "HSP/热激蛋白": r"heat shock|dnaJ|hsp\d|hsc70|chaperon",
    "滞育/光周期": r"diapause|circadian|clock|timeless|cryptochrome|juvenile hormone|ecdysone|vitellogenin",
    "氧化应激": r"catalase|peroxidase|superoxide|glutathione|peroxiredoxin|thioredoxin|cytochrome p450",
}


def load_genes():
    genes = {}
    with gzip.open(GFF, "rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 9 or p[2] != "gene":
                continue
            m = re.search(r"Name=([^;]+)", p[8])
            d = re.search(r"description=([^;]+)", p[8])
            genes.setdefault(p[0], []).append(
                (int(p[3]), int(p[4]), m.group(1) if m else "",
                 (d.group(1) if d else "").replace("%2C", ",")))
    for c in genes:
        genes[c].sort()
    return genes


def main():
    genes = load_genes()
    total_genes = sum(len(v) for v in genes.values())
    print("基因总数 %d" % total_genes)

    gene_sets = {}
    zs = {}
    for g in GROUPS:
        f = os.path.join(REP, "crossregion_z_%s%s.tsv" % (g, SUFFIX))
        if not os.path.exists(f):
            continue
        d = pd.read_csv(f, sep="\t")
        z = d["z"].values.astype(float)
        mk = d["marker"].values
        zs[g] = (mk, z)
        thr = np.quantile(np.abs(z), 1 - TOPF)
        sel = np.where(np.abs(z) >= thr)[0]
        hit = set()
        for i in sel:
            s = str(mk[i])
            c, ps = s.rsplit("_", 1)
            pos = int(ps)
            if c not in genes:
                continue
            for (st, en, name, desc) in genes[c]:
                if st - WIN <= pos <= en + WIN:
                    hit.add(name)
        gene_sets[g] = hit
        print("  %-6s top %d 位点 → %d 个基因" % (g, len(sel), len(hit)))

    # ---- 两两重叠 + 超几何检验 ----
    gs = [g for g in GROUPS if g in gene_sets]
    print()
    print("=== 各地区候选基因集的两两重叠（超几何检验）===")
    print("%-7s" % "" + "".join("%14s" % g for g in gs))
    mat = np.zeros((len(gs), len(gs)), int)
    for i, a in enumerate(gs):
        line = "%-7s" % a
        for j, b in enumerate(gs):
            k = len(gene_sets[a] & gene_sets[b])
            mat[i, j] = k
            if i == j:
                line += "%14s" % ("(%d)" % len(gene_sets[a]))
            else:
                exp = len(gene_sets[a]) * len(gene_sets[b]) / total_genes
                p = hypergeom.sf(k - 1, total_genes, len(gene_sets[a]), len(gene_sets[b]))
                line += "%14s" % ("%d (%.1fx,p%.0e)" % (k, k / max(exp, 1e-9), p))
        print(line)

    # ---- 共同基因 ----
    cnt = {}
    for a in gs:
        for x in gene_sets[a]:
            cnt[x] = cnt.get(x, 0) + 1
    shared = sorted([k for k, v in cnt.items() if v >= 3], key=lambda k: -cnt[k])
    print()
    print("=== 出现在 ≥3 个地区的候选基因：%d 个 ===" % len(shared))
    gdesc = {}
    for c, lst in genes.items():
        for (st, en, name, desc) in lst:
            gdesc[name] = desc
    for x in shared[:25]:
        tag = ";".join(k for k, p in MODULES.items() if re.search(p, gdesc.get(x, ""), re.I))
        print("  %-20s %d 地区  %-46s %s" % (x, cnt[x], gdesc.get(x, "")[:46], tag))

    # ---- 各地区的功能模块富集（位点级 + 置换检验，与 module_enrich.py 同口径）----
    print()
    print("=== 各地区：功能模块富集（位点级 |z|，置换 2000 次）===")
    rng = np.random.default_rng(7)
    print("%-7s %-14s %8s %8s %8s" % ("地区", "模块", "模块|z|", "背景", "置换p"))
    for g in gs:
        mk, z = zs[g]
        az = np.abs(z)
        posv = np.array([int(str(s).rsplit("_", 1)[1]) for s in mk])
        byc = {}
        for i, s in enumerate(mk):
            c = str(s).rsplit("_", 1)[0]
            byc.setdefault(c, []).append(i)
        for mname, pat in MODULES.items():
            idx = []
            for c, lst in genes.items():
                if c not in byc:
                    continue
                ai = np.array(byc[c])
                ap = posv[ai]
                for (st, en, nm, de) in lst:
                    if not re.search(pat, de, re.I):
                        continue
                    m2 = (ap >= st - WIN) & (ap <= en + WIN)
                    idx.extend(ai[m2].tolist())
            idx = np.array(sorted(set(idx)))
            if len(idx) < 5:
                continue
            obs = az[idx].mean()
            nperm_hit = 0
            for _ in range(2000):
                r = rng.choice(len(az), size=len(idx), replace=False)
                if az[r].mean() >= obs:
                    nperm_hit += 1
            p = (nperm_hit + 1) / 2001
            flag = " *" if p < 0.01 else ("  ." if p < 0.05 else "")
            print("%-7s %-14s %8.3f %8.3f %8.4f%s" % (g, mname, obs, az.mean(), p, flag))
    print("  （背景取该地区全部位点的 |z| 均值；* = p<0.01）")

    # ---- 输出基因×地区矩阵 ----
    with open(OUTG, "w", encoding="utf-8") as fh:
        fh.write("gene\tdescription\tn_region\t" + "\t".join(gs) + "\n")
        for x in sorted(cnt, key=lambda k: -cnt[k]):
            fh.write("%s\t%s\t%d\t" % (x, gdesc.get(x, "")[:100], cnt[x])
                     + "\t".join("1" if x in gene_sets[a] else "0" for a in gs) + "\n")
    print()
    print("已写出: %s" % OUTG)

    # ---- 图 ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(13.5, 5.0))
    im = ax[0].imshow(mat, cmap="Reds")
    ax[0].set_xticks(range(len(gs))); ax[0].set_xticklabels(gs)
    ax[0].set_yticks(range(len(gs))); ax[0].set_yticklabels(gs)
    for i in range(len(gs)):
        for j in range(len(gs)):
            ax[0].text(j, i, str(mat[i, j]), ha="center", va="center", fontsize=9,
                       color="white" if mat[i, j] > mat.max() * .6 else "black")
    ax[0].set_title("Overlap of candidate gene sets\n(hypergeometric; same-threshold per region)", fontsize=10)
    plt.colorbar(im, ax=ax[0], fraction=.046)

    nreg = [cnt[x] for x in cnt]
    from collections import Counter
    c2 = Counter(nreg)
    ax[1].bar([str(k) for k in sorted(c2)], [c2[k] for k in sorted(c2)], color="#2980b9")
    for i, k in enumerate(sorted(c2)):
        ax[1].text(i, c2[k], str(c2[k]), ha="center", va="bottom", fontsize=9)
    ax[1].set_xlabel("Number of regions sharing the gene")
    ax[1].set_ylabel("Genes")
    ax[1].set_title("How many regions share each candidate gene", fontsize=10)
    plt.tight_layout()
    plt.savefig(OUTP, dpi=140)
    print("已写出: %s" % OUTP)


if __name__ == "__main__":
    main()
