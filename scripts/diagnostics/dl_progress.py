import os, re, csv, collections

RAW = r"C:\SF_data\01_raw"
TOOLS = r"C:\SF_data\tools"

# 本地已有的 run（成品 / 裸partial / 分片 都算"有数据"）
have_done = set()      # 完整 gzip 成品
have_partial = set()   # 只有裸 partial（截断待修）
have_chunk = set()     # 只有分片
for f in os.listdir(RAW):
    m = re.match(r'^((?:SRR|ERR|DRR)\d+)_([12])\.fastq\.gz$', f)
    if m and os.path.getsize(os.path.join(RAW, f)) > 1024 * 1024:
        have_done.add(m.group(1)); continue
    m = re.match(r'^((?:SRR|ERR|DRR)\d+)_([12])\.fastq\.gz\.partial\d+$', f)
    if m:
        have_partial.add(m.group(1)); continue
    m = re.match(r'^((?:SRR|ERR|DRR)\d+)_([12])\.fastq\.gz\.partial\d+\.part\d+$', f)
    if m:
        have_chunk.add(m.group(1))

have_any = have_done | have_partial | have_chunk

def load(fn):
    p = os.path.join(TOOLS, fn)
    if not os.path.exists(p):
        return None, []
    rows = []
    with open(p, encoding='utf-8') as fh:
        rd = csv.DictReader(fh, delimiter='\t')
        for r in rd:
            rows.append(r)
    return rows

for name in ('batch1_picks.tsv', 'batch2_picks.tsv'):
    rows = load(name)
    if rows is None:
        print(f"{name}: 不存在"); continue
    runs = [r.get('run') or r.get('Run') for r in rows]
    done = [r for r in runs if r in have_done]
    part = [r for r in runs if r in have_partial and r not in have_done]
    chk = [r for r in runs if r in have_chunk and r not in have_done and r not in have_partial]
    none = [r for r in runs if r not in have_any]
    print(f"\n=== {name}  共 {len(runs)} 个 ===")
    print(f"  ✅ 完整成品   : {len(done):3d}")
    print(f"  🔧 待修partial: {len(part):3d}")
    print(f"  📦 仅分片     : {len(chk):3d}")
    print(f"  ⬜ 完全未下   : {len(none):3d}")
    reg = collections.Counter(r.get('region', '?') for r in rows if (r.get('run') or r.get('Run')) in have_any)
    print(f"  已下(任意状态)地区分布: {dict(reg)}")

print(f"\n总览: 成品 {len(have_done)} / 待修 {len(have_partial)} / 仅分片 {len(have_chunk)}")
