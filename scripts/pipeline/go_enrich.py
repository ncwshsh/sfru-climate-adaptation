# -*- coding: utf-8 -*-
"""go_enrich.py —— 候选基因的 GO 功能富集

数据来源（2026-09-24 直连取得，注意：当天代理故障，直连反而可用）：
  - GO 注释：UniProt REST，organism_id:7108（草地贪夜蛾），含 **NCBI GeneID** 交叉引用
    ⇒ 能与我们的 Gnomon 基因（LOC118263360 形式，数字即 GeneID）直接对接
  - GO 本体：go-basic.obo（48,340 个 term），用于取名称与命名空间
  - ⚠️ KEGG 无草地贪夜蛾基因组条目（只有斜纹夜蛾 S. litura），故未做 KEGG 富集

统计：超几何检验（单尾），背景 = "有 GO 注释且在分析范围内的基因"，
      每个命名空间（BP/MF/CC）分别做 BH-FDR。
"""
import os
import re
import gzip
import numpy as np
import pandas as pd
from scipy.stats import hypergeom

ROOT = "/mnt/c/SF_data"
REP = os.path.join(ROOT, "tools", "report")
GODIR = "/home/hugo/data/geneontology"
GFF = os.path.join(ROOT, "00_ref", "GCF_023101765.2_genomic.gff.gz")
UNI = os.path.join(GODIR, "uniprot_sfru_go.tsv")
OBO = os.path.join(GODIR, "go-basic.obo")
OUTDIR = os.path.join(REP, "pub")
FDR = 0.05
MIN_GENES = 3          # 富集结果至少要包含 3 个基因，否则不报（避免单基因噪声）


def parse_obo():
    names, ns = {}, {}
    tid = None
    with open(OBO, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line == "[Term]":
                tid = None
            elif line.startswith("id: GO:"):
                tid = line[4:]
            elif tid and line.startswith("name: "):
                names[tid] = line[6:]
            elif tid and line.startswith("namespace: "):
                ns[tid] = line[11:]
            elif line == "":
                tid = None
    return names, ns


def parse_uniprot():
    """返回 geneid(str) -> set(GO)"""
    g2go = {}
    for i, line in enumerate(open(UNI, encoding="utf-8")):
        if i == 0:
            continue
        p = line.rstrip("\n").split("\t")
        if len(p) < 9:
            continue
        go = p[4]
        gid = p[8]
        if not go or not gid:
            continue
        ids = [x.strip() for x in gid.split(";") if x.strip().isdigit()]
        if not ids:
            continue
        terms = set(x.strip() for x in go.split(";") if x.strip().startswith("GO:"))
        for g in ids:
            g2go.setdefault(g, set()).update(terms)
    return g2go


def gff_genes():
    """返回 {LOC 数字: 描述}"""
    genes = {}
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
            d = re.search(r"description=([^;]+)", p[8])
            genes[m.group(1)] = (d.group(1) if d else "").replace("%2C", ",")
    return genes


def loc_num(name):
    m = re.search(r"LOC(\d+)", str(name))
    return m.group(1) if m else None


def enrich(fore_genes, back_genes, g2go, names, ns, tag):
    """超几何富集；返回 DataFrame"""
    fore = set(g for g in fore_genes if g in g2go)
    back = set(g for g in back_genes if g in g2go)
    N, n = len(back), len(fore)
    print("  [%s] 前景 %d（有注释 %d）/ 背景 %d" % (tag, len(fore_genes), n, N))
    rows = []
    allterms = set()
    for g in fore:
        allterms.update(g2go[g])
    for t in allterms:
        inback = sum(1 for g in back if t in g2go[g])
        info = sum(1 for g in fore if t in g2go[g])
        if info < MIN_GENES or inback < MIN_GENES:
            continue
        p = float(hypergeom.sf(info - 1, N, inback, n))
        exp = n * inback / N
        rows.append(dict(go=t, name=names.get(t, ""), namespace=ns.get(t, ""),
                         n_info=info, n_back=inback, expected=exp,
                         fold=info / exp if exp else np.nan, p=p))
    if not rows:
        print("  [%s] 无通过最小基因数门槛的 GO 项" % tag)
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # 按命名空间分别做 BH-FDR
    df["fdr"] = np.nan
    for nsm, sub in df.groupby("namespace"):
        o = sub["p"].argsort().values
        m = len(sub)
        q = sub["p"].values[o] * m / (np.arange(1, m + 1))
        q = np.minimum.accumulate(q[::-1])[::-1]
        df.loc[sub.index[o], "fdr"] = q
    df = df.sort_values("p")
    out = os.path.join(REP, "go_enrichment_%s.tsv" % tag)
    df.to_csv(out, sep="\t", index=False)
    print("  已写出: %s" % out)
    sig = df[df["fdr"] < FDR]
    print("  FDR<%.2f 的 GO 项：%d 个" % (FDR, len(sig)))
    for _, r in sig.head(12).iterrows():
        print("    %-12s %-8s %2d/%-4d x%.1f  %s"
              % (r["go"], r["namespace"][:8], r["n_info"], r["n_back"], r["fold"], r["name"][:52]))
    return df


def main():
    print("解析 GO 本体…")
    names, ns = parse_obo()
    print("解析 UniProt 注释…")
    g2go = parse_uniprot()
    print("  有 GO 注释的 GeneID 数: %d" % len(g2go))
    genes = gff_genes()
    print("GFF 基因数: %d" % len(genes))
    back = [g for g in genes if g in g2go]
    print("  有注释的背景基因: %d" % len(back))

    # ---- 前景 1：所有候选位点（|z|>4）映射到的基因 ----
    cand = pd.read_csv(os.path.join(REP, "gea_candidates_full_annotated.tsv"), sep="\t")
    f1 = set(loc_num(x) for x in cand["gene"] if loc_num(x))
    print()
    print("=== 候选位点基因集（|z|>4, %d 个位点）===" % len(cand))
    enrich(f1, back, g2go, names, ns, "candidates")

    # ---- 前景 2：FDR 严格显著的位点基因 ----
    fdr = pd.read_csv(os.path.join(REP, "gea_fdr_significant_annotated.tsv"), sep="\t")
    f2 = set(loc_num(x) for x in fdr["gene"] if loc_num(x))
    print()
    print("=== FDR 显著位点基因集（%d 个位点 → %d 个基因）===" % (len(fdr), len(f2)))
    enrich(f2, back, g2go, names, ns, "fdr_significant")

    # ---- 前景 3：跨地区共享基因（≥3 个地区）----
    sh = pd.read_csv(os.path.join(REP, "crossregion_genes.tsv"), sep="\t")
    sh = sh[sh["n_region"] >= 3]
    f3 = set(loc_num(x) for x in sh["gene"] if loc_num(x))
    print()
    print("=== 跨地区共享基因集（≥3 地区, %d 个）===" % len(f3))
    enrich(f3, back, g2go, names, ns, "shared")


if __name__ == "__main__":
    main()
