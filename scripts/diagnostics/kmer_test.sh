#!/bin/bash
# 目的: 用 alignment-free 的 k-mer 包含率独立判断"样本 vs 参考"的真实序列差异
# 原理: 若每碱基差异率为 d, 则长度 K 的 k-mer 完全匹配概率 = (1-d)^K
#       实测包含率 c  ->  d_est = 1 - c^(1/K)
# 该方法不使用任何比对器, 因此不受比对偏倚/NM 计算方式影响
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
set -u

REF=""
for c in /home/hugo/data/ref/ref_GCF_023101765.2.fna \
         /home/hugo/data/03_align/ref_GCF_023101765.2.fna \
         /mnt/c/SF_data/03_align/ref_GCF_023101765.2.fna; do
  [ -f "$c" ] && REF="$c" && break
done
echo "REF=$REF"
[ -z "$REF" ] && { echo "[ERR] 找不到参考基因组"; exit 1; }
[ -f "${REF}.fai" ] || samtools faidx "$REF"

CHR=$(cut -f1 "${REF}.fai" | head -1)
echo "CHR=$CHR  (fai 首行)"

REG="${CHR}:1-3000000"
samtools faidx "$REF" "$REG" > /tmp/ref_reg.fa
echo "参考区段碱基数: $(grep -v '^>' /tmp/ref_reg.fa | tr -d '\n' | wc -c)"

for S in SRR11528381 SRR12044628; do
  BAM="/home/hugo/data/03_align/${S}.dedup.bam"
  [ -f "$BAM" ] || { echo "[skip] $S 无 bam"; continue; }
  samtools view -h "$BAM" "$REG" 2>/dev/null | samtools fasta - 2>/dev/null \
    | head -400000 > "/tmp/reads_${S}.fa"
  echo "$S 取样 reads = $(grep -c '^>' "/tmp/reads_${S}.fa")"
done

# 顺带确认真实碱基质量(限定误差贡献的上界)
R1=/home/hugo/data/01_raw/SRR11528381_1.fastq.gz
if [ -f "$R1" ]; then
  echo "--- 前 20 万条 read 的平均碱基质量 ---"
  pigz -dc "$R1" 2>/dev/null | head -800000 | awk '
    BEGIN{ for(q=0;q<=41;q++) V[sprintf("%c",q+33)]=q }
    NR%4==0 { for(i=1;i<=length($0);i++){ c=substr($0,i,1); s+=V[c]; n++ } }
    END{ if(n>0) printf "平均 Q = %.2f  (约合错误率 %.4f%%)\n", s/n, 100*10^(-(s/n)/10) }'
fi

python3 - <<'PY'
K = 21
ENC = {'A':0,'C':1,'G':2,'T':3}
MASK = (1 << (2*K)) - 1

def khashes(seq):
    v = 0; n = 0
    for ch in seq:
        c = ENC.get(ch)
        if c is None:
            v = 0; n = 0; continue
        v = ((v << 2) | c) & MASK
        n += 1
        if n >= K:
            yield v

def readfa(p):
    name = None; buf = []
    for line in open(p):
        if line[0] == '>':
            if name is not None: yield ''.join(buf)
            name = line[1:].strip(); buf = []
        else:
            buf.append(line.strip().upper())
    if name is not None: yield ''.join(buf)

refseq = ''.join(readfa('/tmp/ref_reg.fa'))
print(f"参考区段长度 = {len(refseq):,} bp")
refset = set(khashes(refseq))
print(f"参考 k-mer 种类数 = {len(refset):,} (K={K})")

def containment(fa, limit=None):
    tot = 0; hit = 0
    for i, s in enumerate(readfa(fa)):
        if limit and i >= limit: break
        for h in khashes(s):
            tot += 1
            if h in refset: hit += 1
    return hit, tot

# 内部对照: 参考自己切成的 150 bp 伪读 -> 应当 100% 命中
ctrl = [refseq[i:i+150] for i in range(0, 300000, 150)]
ct = 0; ch = 0
for s in ctrl:
    for h in khashes(s):
        ct += 1
        if h in refset: ch += 1
print(f"\n[内部对照] 参考自身伪读 包含率 = {ch/ct:.4f}  (期望 1.0000)")

import os
for s in ['SRR11528381','SRR12044628']:
    p = f'/tmp/reads_{s}.fa'
    if not os.path.exists(p): continue
    hit, tot = containment(p, limit=200000)
    c = hit/tot
    d = 1 - c ** (1.0/K)
    print(f"\n[{s}]  read k-mer 数 = {tot:,}  命中 = {hit:,}")
    print(f"          包含率 c = {c:.4f}   ->  估计每碱基差异 d = {d*100:.3f}%")
PY
