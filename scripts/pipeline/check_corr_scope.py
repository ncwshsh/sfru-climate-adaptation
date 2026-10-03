# -*- coding: utf-8 -*-
"""复核稿件中所有纬度相关系数的「口径」——纯标准库。

两个候选口径：
  A) qc_s2_bm2k15.tsv   —— 全 220 下载样本（pre-exclusion）
  B) gea_input.tsv      —— 214 分析队列（稿件正文声称用的表）
"""
import io, math

def pearson(xs, ys):
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    sxx = math.sqrt(sum((x-mx)**2 for x in xs))
    syy = math.sqrt(sum((y-my)**2 for y in ys))
    return sxy/(sxx*syy)

def rank(xs):
    idx = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0]*len(xs); i = 0
    while i < len(idx):
        j = i
        while j+1 < len(idx) and xs[idx[j+1]] == xs[idx[i]]:
            j += 1
        avg = (i+j)/2 + 1
        for k in range(i, j+1):
            r[idx[k]] = avg
        i = j+1
    return r

def spearman(xs, ys):
    return pearson(rank(xs), rank(ys))

def load(path):
    with io.open(path, encoding='utf-8') as f:
        head = f.readline().rstrip('\n').split('\t')
        return [dict(zip(head, ln.rstrip('\n').split('\t'))) for ln in f]

qc  = load(r'C:\SF_data\tools\report\qc_s2_bm2k15.tsv')   # 220
gea = load(r'C:\SF_data\tools\report\gea_input.tsv')      # 214

print(f'qc rows = {len(qc)}, gea rows = {len(gea)}')

def col(rows, name, cast=float):
    return [cast(r[name]) for r in rows]

def report(tag, rows):
    lat  = col(rows, 'lat')
    rate = col(rows, 'rate')
    dep  = col(rows, 'raw_depth')
    print(f'--- {tag} (n={len(rows)}) ---')
    print(f'  rate~lat : Pearson {pearson(rate, lat):+.4f} | Spearman {spearman(rate, lat):+.4f}')
    print(f'  dep ~lat : Pearson {pearson(dep,  lat):+.4f} | Spearman {spearman(dep,  lat):+.4f}')
    for m in ('US', 'BR'):
        sub = [r for r in rows if r['module'] == m]
        if not sub:
            continue
        la = col(sub, 'lat'); ra = col(sub, 'rate'); de = col(sub, 'raw_depth')
        print(f'  {m:2s} n={len(sub):3d}: rate~lat P {pearson(ra, la):+.4f} | dep~lat P {pearson(de, la):+.4f}')
    # BIO correlations only exist in gea_input
    if 'bio1' in rows[0]:
        b1  = col(rows, 'bio1')
        b11 = col(rows, 'bio11')
        us = [r for r in rows if r['module'] == 'US']
        if us:
            lu = col(us, 'lat'); u1 = col(us, 'bio1'); u11 = col(us, 'bio11')
            print(f'  US bio1~lat  Pearson {pearson(lu, u1):+.4f} | Spearman {spearman(lu, u1):+.4f}')
            print(f'  US bio11~lat Pearson {pearson(lu, u11):+.4f} | Spearman {spearman(lu, u11):+.4f}')
    print()

report('A) qc_s2_bm2k15 (全 220)', qc)
report('B) gea_input (分析 214)', gea)

# 找出 220 与 214 的差集，看剔掉的是谁
qc_runs  = set(r['run'] for r in qc)
gea_runs = set(r['run'] for r in gea)
diff = sorted(qc_runs - gea_runs)
print('220 中被剔除的 6 个样本:')
for run in diff:
    r = [x for x in qc if x['run'] == run][0]
    print(f"  {run}  module={r['module']}  lat={r['lat']}  rate={r['rate']}")

# 用 220 表重算 US 面板 BIO 相关不可行（无 bio 列），
# 但可以看：剔除 6 个后 rate~lat 全队列变化
