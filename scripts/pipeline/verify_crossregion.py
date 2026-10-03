# -*- coding: utf-8 -*-
r"""verify_crossregion.py —— 用纯标准库复算 crossregion_genes.py 的可精确验证部分

目的：
  1. 验证英文稿 §3.9 报的"两两基因集重叠 / 富集倍数 / 超几何 p / 550 个共享基因"能否复现
  2. 提供一个不依赖 numpy 的校验器，将来换了 z 文件（如剔除低比对率样本后）可立即复算对照

只复算**精确、廉价**的部分（集合运算 + 超几何检验）。
模块富集那部分用的是 2000 次置换抽样，纯 Python 太慢，仍由 WSL 侧脚本重跑。
"""
import os, re, gzip, sys, math
from itertools import combinations

sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'C:\SF_data'
GFF  = os.path.join(ROOT, '00_ref', 'GCF_023101765.2_genomic.gff.gz')
REP  = os.path.join(ROOT, 'tools', 'report')
GROUPS = ['US-C', 'BR-C', 'AF-C', 'AM-C', 'CN-C']
WIN = 2000
TOPF = 0.002
# 可选：命令行传后缀（如 `_excl3`）即复算敏感性分析的 z 文件
SUFFIX = sys.argv[1] if len(sys.argv) > 1 else ''


def load_genes():
    genes = {}
    with gzip.open(GFF, 'rt', encoding='utf-8', errors='ignore') as fh:
        for line in fh:
            if line.startswith('#'):
                continue
            p = line.rstrip('\n').split('\t')
            if len(p) < 9 or p[2] != 'gene':
                continue
            m = re.search(r'Name=([^;]+)', p[8])
            genes.setdefault(p[0], []).append(
                (int(p[3]), int(p[4]), m.group(1) if m else ''))
    for c in genes:
        genes[c].sort()
    return genes


def lchoose(n, k):
    if k < 0 or k > n:
        return float('-inf')
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def hyper_sf(k, M, n, N):
    """P(X >= k), X ~ Hypergeom(M, n, N)  —— 对应 scipy.stats.hypergeom.sf(k-1, M, n, N)"""
    if k <= 0:
        return 1.0
    kmax = min(n, N)
    if k > kmax:
        return 0.0
    lden = lchoose(M, N)
    tot = 0.0
    for i in range(k, kmax + 1):
        a = lchoose(n, i)
        b = lchoose(M - n, N - i)
        if a == float('-inf') or b == float('-inf'):
            continue
        tot += math.exp(a + b - lden)
    return min(1.0, tot)


def quantile(sorted_vals, q):
    """numpy 的 linear 插值分位，用于复现 np.quantile"""
    if not sorted_vals:
        return None
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def main():
    genes = load_genes()
    total_genes = sum(len(v) for v in genes.values())
    print('基因总数（全部 gene 特征）: %d' % total_genes)

    gene_sets = {}
    zs = {}
    print()
    print('%-7s %10s %12s' % ('组', 'top位点', '映射基因'))
    for g in GROUPS:
        f = os.path.join(REP, 'crossregion_z_%s%s.tsv' % (g, SUFFIX))
        if not os.path.exists(f):
            print('  %s: 缺文件' % g); continue
        mk, z = [], []
        with open(f, encoding='utf-8') as fh:
            next(fh)
            for line in fh:
                a, b = line.rstrip('\n').split('\t')
                mk.append(a); z.append(float(b))
        zs[g] = (mk, z)
        az = sorted(abs(v) for v in z)
        thr = quantile(az, 1 - TOPF)
        sel = [i for i, v in enumerate(z) if abs(v) >= thr]
        hit = set()
        for i in sel:
            s = mk[i]
            c, ps = s.rsplit('_', 1)
            pos = int(ps)
            lst = genes.get(c)
            if not lst:
                continue
            for (st, en, name) in lst:
                if st - WIN <= pos <= en + WIN:
                    hit.add(name)
        gene_sets[g] = hit
        print('%-7s %10d %12d' % (g, len(sel), len(hit)))

    gs = [g for g in GROUPS if g in gene_sets]

    print()
    print('=== 两两重叠（超几何检验）===')
    got = {}
    for a, b in combinations(gs, 2):
        ka, kb = gene_sets[a], gene_sets[b]
        k = len(ka & kb)
        exp = len(ka) * len(kb) / total_genes
        p = hyper_sf(k, total_genes, len(ka), len(kb))
        fac = k / max(exp, 1e-9)
        got[(a, b)] = (k, fac, p)
        print('  %-6s ∩ %-6s : %4d 基因   %.1f×   p = %.0e' % (a, b, k, fac, p))

    cnt = {}
    for a in gs:
        for x in gene_sets[a]:
            cnt[x] = cnt.get(x, 0) + 1
    shared3 = [x for x, v in cnt.items() if v >= 3]
    print()
    print('=== 出现在 >=3 个地区的共享基因: %d 个 ===' % len(shared3))
    from collections import Counter
    print('  按共享地区数分布: %s' % dict(sorted(Counter(cnt.values()).items())))

    print()
    if SUFFIX:
        print('（后缀 %s：跳过与英文稿原值的对照，仅复算）' % SUFFIX)
        print('  各面板基因集: %s' % ' | '.join('%s=%d' % (g, len(gene_sets[g])) for g in gs))
        return
    print('=== 与英文稿 §3.9 的对照 ===')
    EXPECT = {('AM-C', 'BR-C'): 434, ('US-C', 'BR-C'): 419, ('US-C', 'AM-C'): 397,
              ('CN-C', 'BR-C'): 357, ('AF-C', 'US-C'): 258}
    ok = True
    for (a, b), v in EXPECT.items():
        gotv = got.get((a, b)) or got.get((b, a))
        if gotv is None:
            print('  %-14s 稿  %4d  →  未算出' % ('%s∩%s' % (a, b), v)); ok = False
            continue
        mark = 'OK' if gotv[0] == v else '★ 不一致'
        if gotv[0] != v:
            ok = False
        print('  %-14s 稿  %4d  |  算  %4d   %s' % ('%s∩%s' % (a, b), v, gotv[0], mark))
    mark = 'OK' if len(shared3) == 550 else '★ 不一致'
    if len(shared3) != 550:
        ok = False
    print('  %-14s 稿   550  |  算  %4d   %s' % ('>=3 地区共享', len(shared3), mark))
    print()
    print('  ⇒ 总体: %s' % ('全部复现 ✓' if ok else '存在不一致，见 ★'))


if __name__ == '__main__':
    main()
