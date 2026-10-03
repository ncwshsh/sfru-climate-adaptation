import os, re, csv, collections

RAW = r"C:\SF_data\01_raw"
MATRIX = r"C:\SF_data\tools\sfru_wgs_matrix.tsv"

# 1) 收集本地已有的 run（成品或裸 partial 都算）
have = set()
for f in os.listdir(RAW):
    m = re.match(r'^(SRR|ERR|DRR)\d+', f)
    if m:
        have.add(m.group(1) + m.group(0)[3:] if False else m.group(0))
have = set()
for f in os.listdir(RAW):
    m = re.match(r'^((?:SRR|ERR|DRR)\d+)_', f)
    if m:
        have.add(m.group(1))

# 2) 读矩阵
info = {}
with open(MATRIX, encoding='utf-8') as fh:
    rd = csv.DictReader(fh, delimiter='\t')
    for r in rd:
        info[r['run']] = r

print(f"本地已有样本(run): {len(have)}")
rows = [info[r] for r in have if r in info]
miss = [r for r in have if r not in info]
print(f"矩阵中匹配到: {len(rows)}   未匹配: {len(miss)}")
if miss:
    print("  未匹配(前10):", miss[:10])

# 3) 地区/国家分布
c = collections.Counter((r.get('region', '?'), r.get('country', '?')) for r in rows)
print("\n=== 地区 × 国家 分布 ===")
for (reg, ctry), n in sorted(c.items(), key=lambda x: (-x[1], x[0])):
    print(f"  {n:3d}  {reg:<14} {ctry}")

# 4) 深度分布（原始深度）
ds = sorted(float(r['depth_x']) for r in rows if r.get('depth_x'))
if ds:
    import statistics
    print(f"\n原始深度: n={len(ds)} 中位={statistics.median(ds):.1f}x  最小={ds[0]:.1f}x  最大={ds[-1]:.1f}x")
    tgt = [min(10.0, d) for d in ds]
    print(f"截取后目标深度: 中位={statistics.median(tgt):.1f}x  最小={min(tgt):.1f}x")
    print(f"  <10x 的样本数(截取后达不到10x): {sum(1 for d in ds if d < 10)}")

# 5) study 分布
print("\n=== study 分布 (前10) ===")
for s, n in collections.Counter(r['study'] for r in rows).most_common(10):
    print(f"  {n:3d}  {s}")
