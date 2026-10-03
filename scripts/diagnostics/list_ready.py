import os, re, csv, collections

RAW = r"C:\SF_data\01_raw"
MATRIX = r"C:\SF_data\tools\sfru_wgs_matrix.tsv"

# 成品 = 修复好的完整 gzip
pairs = collections.defaultdict(set)
single = collections.defaultdict(set)
for f in os.listdir(RAW):
    m = re.match(r'^((?:SRR|ERR|DRR)\d+)_([12])\.fastq\.gz$', f)
    if not m:
        continue
    run, mate = m.group(1), m.group(2)
    sz = os.path.getsize(os.path.join(RAW, f))
    if sz < 1024 * 1024:      # 小于 1MB 视为残缺
        continue
    pairs[run].add(mate)

both = sorted(r for r, m in pairs.items() if m == {'1', '2'})
only_one = sorted(r for r, m in pairs.items() if len(m) == 1)

mat = {}
with open(MATRIX, encoding='utf-8') as fh:
    for r in csv.DictReader(fh, delimiter='\t'):
        mat[r['run']] = r

print(f"双端齐全、可比对样本: {len(both)}")
print(f"仅单端（暂不用）   : {len(only_one)}")
if only_one:
    print("   ", ", ".join(only_one[:12]), "..." if len(only_one) > 12 else "")

# 地区分布
c = collections.Counter(mat[r].get('region', '?') for r in both if r in mat)
print("\n=== 可比对样本的地区分布 ===")
for k, v in c.most_common():
    print(f"  {v:3d}  {k}")

# 按地区挑样例用于快速验证
print("\n=== 建议先用这 12 个做 Ts/Tv 快速验证（跨地区）===")
byreg = collections.defaultdict(list)
for r in both:
    if r in mat:
        byreg[mat[r].get('region', '?')].append(r)
for reg in byreg:
    print(f"  {reg}: {', '.join(byreg[reg][:4])}")

# 输出完整列表
with open(r"C:\SF_data\tools\ready_samples.txt", "w") as fh:
    for r in both:
        fh.write(r + "\n")
print(f"\n完整列表已写入: C:\\SF_data\\tools\\ready_samples.txt  ({len(both)} 个)")
