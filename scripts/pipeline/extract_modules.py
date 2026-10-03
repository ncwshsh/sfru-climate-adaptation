#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 GCF_023101765.2 GFF 提取 HSP/滞育-光周期/氧化应激 三功能模块基因坐标"""
import gzip, re, csv, os

GFF = r"C:\SF_data\00_ref\GCF_023101765.2_genomic.gff.gz"
OUTDIR = r"C:\SF_data\00_ref"

# 功能模块关键词(基因名/基因家族), 大小写不敏感
MODULES = {
  'HSP': [r'hsp', r'heat.shock', r'hsc', r'groel', r'hsp70', r'hsp90', r'hsp60', r'dna.j'],
  'Dormancy_Photo': [r'clock', r'^per\b', r'period', r'cry', r'cryptochrome', r'timless', r'timeless',
                     r'vpac', r'ptth', r'chorion', r'egg.vitell', r'juv.', r'ecdl', r'ecdys',
                     r'pi3k', r'akt', r'mtor', r'brd9', r'brat', r'bric', r'king', r'ft\b', r'time'],
  'OxStress': [r'sod', r'superoxide', r'catalase', r'\bcatalase', r'gpx', r'glutathione.per', r'prx',
               r'peroxiredoxin', r'gst', r'glutathione.s.transfer', r'\bnox\b', r'nadph',
               r'ferredoxin', r'thioredoxin', r'\btrx\b', r'glycine.rad'],
}
# 预编译
pats = {m:[re.compile(p, re.I) for p in pats_] for m,pats_ in MODULES.items()}

gene_rows = []   # 基因级
trans_rows = []  # 转录本/蛋白级(带家族标签)
n_total_gene = 0
with gzip.open(GFF, 'rt', encoding='utf-8', errors='replace') as f:
    for line in f:
        if line[0] == '#' or not line.strip():
            continue
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 9: continue
        seqid, source, feat, start, end, score, strand, phase, attr = parts[:9]
        # 解析属性
        am = re.search(r'gene_id\s+"([^"]+)"', attr)
        gn = re.search(r'Name\s+"([^"]+)"', attr) or re.search(r'gene\s+"([^"]+)"', attr)
        pf = re.search(r'gene_name\s+"([^"]+)"', attr)
        name = (am or gn or pf).group(1) if (am or gn or pf) else ''
        # 产品/转录本名
        prod = re.search(r'product\s+"([^"]+)"', attr)
        product = prod.group(1) if prod else ''

        if feat == 'gene':
            n_total_gene += 1
            gene_rows.append({'gene_id':name,'seqid':seqid,'start':int(start),'end':int(end),
                              'strand':strand,'len':int(end)-int(start)+1,'product':product})

print(f"基因总数: {n_total_gene}")

# 归类(按 gene 的 gene_id + product 名匹配)
module_genes = {m:[] for m in MODULES}
unmatched = 0
for g in gene_rows:
    text = g['gene_id'] + ' ' + g['product']
    hit = None
    for m, pats_ in pats.items():
        if any(p.search(text) for p in pats_):
            hit = m; break
    if hit:
        g['module'] = hit
        module_genes[hit].append(g)
    else:
        unmatched += 1

print("\n=== 功能模块基因命中 ===")
for m in MODULES:
    print(f"  {m}: {len(module_genes[m])} genes")
print(f"  (未归类: {unmatched})")

# 写 CSV
os.makedirs(OUTDIR, exist_ok=True)
for m in MODULES:
    fp = os.path.join(OUTDIR, f"module_{m}.csv")
    with open(fp,'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['gene_id','seqid','start','end','strand','len','product'])
        for g in sorted(module_genes[m], key=lambda x:(x['seqid'],x['start'])):
            w.writerow([g['gene_id'],g['seqid'],g['start'],g['end'],g['strand'],g['len'],g['product']])
    print(f"  -> {fp}")

# 全基因表(备查)
fp = os.path.join(OUTDIR, "all_genes.csv")
with open(fp,'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['gene_id','seqid','start','end','strand','len','product'])
    for g in sorted(gene_rows, key=lambda x:(x['seqid'],x['start'])):
        w.writerow([g['gene_id'],g['seqid'],g['start'],g['end'],g['strand'],g['len'],g['product']])
print(f"  -> {fp} ({len(gene_rows)} genes)")

# 打印各模块前 15 个基因名示例
print("\n=== 各模块基因名示例(前15) ===")
for m in MODULES:
    names = [g['gene_id'] for g in module_genes[m][:15]]
    print(f"  {m}: {names}")
