# -*- coding: utf-8 -*-
"""go_bias_check.py —— 检验候选基因的"基因长度偏差"，并做长度匹配的敏感性分析

为什么要做这一步：
  GO 富集给出的是 plasma membrane / neuron / cell adhesion 这类结果，
  与"温度-氧化应激"的预期完全不符。GEA 领域**已知的假象**是：
  长基因、变异丰富、注释更全的基因更容易被选中（它们承载更多 SNP，
  统计功效天然更高）。若不排除，会把"基因长度"误读成"功能偏好"。

做法：
  1. 比较候选基因 vs 背景基因的长度分布（Mann-Whitney U）
  2. 若差异显著 ⇒ 按长度分层，在每一层内**匹配抽样**背景基因，重做 GO 富集
  3. 若长度匹配后富集信号消失 ⇒ 原结果就是长度偏差，不能作为功能证据
"""
import os
import re
import gzip
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, hypergeom

ROOT = "/mnt/c/SF_data"
REP = os.path.join(ROOT, "tools", "report")
GFF = os.path.join(ROOT, "00_ref", "GCF_023101765.2_genomic.gff.gz")
GODIR = "/home/hugo/data/geneontology"


def gff_genes():
    """{LOC数字: (长度, 描述)}"""
    g = {}
    with gzip.open(GFF, "rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 9 or p[2] != "gene":
                continue
            m = re.search(r"Name=LOC(\d+)", p[8])
            if not m:
                continue
            g[m.group(1)] = int(p[4]) - int(p[3]) + 1
    return g


def loc_num(x):
    m = re.search(r"LOC(\d+)", str(x))
    return m.group(1) if m else None


def main():
    gl = gff_genes()
    cand = pd.read_csv(os.path.join(REP, "gea_candidates_full_annotated.tsv"), sep="\t")
    fore = set(loc_num(x) for x in cand["gene"] if loc_num(x))
    back = set(gl)
    print("候选基因 %d / 全部基因 %d" % (len(fore), len(back)))

    Lf = np.array([gl[g] for g in fore if g in gl])
    Lb = np.array([gl[g] for g in back if g not in fore])
    print()
    print("=== 基因长度比较（bp）===")
    print("  候选基因:  中位 %8.0f  均值 %8.0f  n=%d" % (np.median(Lf), Lf.mean(), len(Lf)))
    print("  其余基因:  中位 %8.0f  均值 %8.0f  n=%d" % (np.median(Lb), Lb.mean(), len(Lb)))
    u, p = mannwhitneyu(Lf, Lb, alternative="greater")
    print("  Mann-Whitney U（候选 > 其余）: p = %.3e   中位数比 = %.2fx"
          % (p, np.median(Lf) / np.median(Lb)))
    if p < 1e-3:
        print("  ⇒ ⚠ **存在明显的基因长度偏差**：长基因更容易被选为候选")
        print("     这不是生物学功能偏好，是统计功效差异（长基因承载更多 SNP）")
    else:
        print("  ⇒ 未见明显长度偏差")

    # ---- 长度匹配抽样 ----
    print()
    print("=== 长度匹配的敏感性分析 ===")
    # 按长度分 10 层，在每层内抽与候选等量的背景基因，重做富集
    bins = np.quantile(Lf, np.linspace(0, 1, 11))
    bins[0], bins[-1] = 0, np.inf
    matched = []
    rng = np.random.default_rng(7)
    for i in range(10):
        lo, hi = bins[i], bins[i + 1]
        need = int(((Lf >= lo) & (Lf <= hi)).sum())
        pool = [g for g in back if g not in fore and lo <= gl[g] <= hi]
        if not pool:
            continue
        k = min(need, len(pool))
        matched.extend(rng.choice(pool, size=k, replace=False).tolist())
    print("  按长度分层匹配得到背景集：%d 个基因（与候选等量、长度分布一致）"
          % len(matched))
    Lm = np.array([gl[g] for g in matched])
    print("  匹配背景的长度：中位 %.0f（候选 %.0f）" % (np.median(Lm), np.median(Lf)))

    # 用匹配背景重跑一次"是否仍在同样的 GO 项上富集"
    uni = os.path.join(GODIR, "uniprot_sfru_go.tsv")
    g2go = {}
    for i, line in enumerate(open(uni, encoding="utf-8")):
        if i == 0:
            continue
        p2 = line.rstrip("\n").split("\t")
        if len(p2) < 9 or not p2[4] or not p2[8]:
            continue
        ids = [x.strip() for x in p2[8].split(";") if x.strip().isdigit()]
        terms = set(x.strip() for x in p2[4].split(";") if x.strip().startswith("GO:"))
        for g in ids:
            g2go.setdefault(g, set()).update(terms)

    def top_terms(fg, bg, ntop=12):
        fore2 = set(g for g in fg if g in g2go)
        back2 = set(g for g in bg if g in g2go)
        N, n = len(back2), len(fore2)
        rows = []
        terms = set()
        for g in fore2:
            terms.update(g2go[g])
        for t in terms:
            ib = sum(1 for g in back2 if t in g2go[g])
            ii = sum(1 for g in fore2 if t in g2go[g])
            if ii < 3 or ib < 3:
                continue
            rows.append((t, ii, ib, float(hypergeom.sf(ii - 1, N, ib, n))))
        rows.sort(key=lambda x: x[3])
        return rows[:ntop], N, n

    r_all, N1, n1 = top_terms(fore, back)
    r_match, N2, n2 = top_terms(fore, matched)
    print()
    print("  原背景（n=%d）top GO:  %s" % (N1, ", ".join(x[0] for x in r_all[:6])))
    print("  匹配背景（n=%d）top GO: %s" % (N2, ", ".join(x[0] for x in r_match[:6])))
    print()
    print("  判读：若两行 top GO 高度重合，说明富集**不只是**长度造成的；")
    print("        若匹配后信号明显减弱/换项，说明原结果主要是长度偏差。")

    pd.DataFrame(r_all, columns=["go", "n_info", "n_back", "p"]).to_csv(
        os.path.join(REP, "go_top_original.tsv"), sep="\t", index=False)
    pd.DataFrame(r_match, columns=["go", "n_info", "n_back", "p"]).to_csv(
        os.path.join(REP, "go_top_lengthmatched.tsv"), sep="\t", index=False)
    print("  已写出 go_top_original.tsv / go_top_lengthmatched.tsv")


if __name__ == "__main__":
    main()
