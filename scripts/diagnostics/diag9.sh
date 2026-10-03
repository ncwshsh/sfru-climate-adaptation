#!/bin/bash
# 决定性检验: 样本↔样本 差异 vs 样本↔参考 差异
# 若 d(A,B) << d(A,ref), 则参考基因组个体是离群点(株系/谱系不匹配)
# 反之若 d(A,B) ≈ d(A,ref), 则高分歧是系统性的、与参考个体无关
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
set -u
REF=/home/hugo/data/ref/ref_GCF_023101765.2.fna
REG=NC_064212.1:1-3000000
A=SRR11528381   # 中国 浙江 (PRJNA590312)
B=SRR12044628   # 美国 PRJNA640063

samtools faidx "$REF" "$REG" > /tmp/ref_reg.fa

for S in $A $B; do
  samtools view -q 40 "/home/hugo/data/03_align/${S}.dedup.bam" "$REG" \
    | awk '$6 ~ /^[0-9]+M$/' \
    | awk 'BEGIN{OFS="\n"} {print ">r"NR; print $10}' | head -400000 > "/tmp/cl_${S}.fa"
  echo "$S 干净 reads = $(( $(grep -c '^>' /tmp/cl_${S}.fa) ))"
done

python3 - <<'PY'
K=21; ENC={'A':0,'C':1,'G':2,'T':3}; MASK=(1<<(2*K))-1
def kh(s):
    v=0;n=0
    for ch in s:
        c=ENC.get(ch)
        if c is None: v=0;n=0;continue
        v=((v<<2)|c)&MASK; n+=1
        if n>=K: yield v
def rf(p):
    nm=None;b=[]
    for l in open(p):
        if l[0]=='>':
            if nm is not None: yield ''.join(b)
            nm=l[1:];b=[]
        else: b.append(l.strip().upper())
    if nm is not None: yield ''.join(b)

refs=''.join(rf('/tmp/ref_reg.fa'))
REF=set(kh(refs))
print(f"参考区段 {len(refs):,} bp, k-mer 种类 {len(REF):,}")

def setof(p, lim=None):
    S=set()
    for i,s in enumerate(rf(p)):
        if lim and i>=lim: break
        S.update(kh(s))
    return S

SA=setof('/tmp/cl_SRR11528381.fa', 100000)
SB=setof('/tmp/cl_SRR12044628.fa', 100000)
print(f"A(SRR11528381) k-mer {len(SA):,}   B(SRR12044628) k-mer {len(SB):,}")

def cont(X, Y, name):
    hit=sum(1 for h in X if h in Y)
    c=hit/len(X); d=1-c**(1.0/K)
    print(f"  {name:<34} c={c:.4f}   d={d*100:.3f}%")
    return d*100

print("\n===== 包含率矩阵 =====")
print(" [自洽对照]")
cont(SA, SA, "A-kmers 在 A 中")
cont(REF, SA, "参考-kmers 在 A 中 (覆盖完整性)")
cont(REF, SB, "参考-kmers 在 B 中 (覆盖完整性)")
print(" [关键比较]")
dAr = cont(SA, REF, "A 的 kmers 在 参考 中  d(A,ref)")
dBr = cont(SB, REF, "B 的 kmers 在 参考 中  d(B,ref)")
dAB = cont(SA, SB,  "A 的 kmers 在 B 中     d(A,B)")
dBA = cont(SB, SA,  "B 的 kmers 在 A 中     d(B,A)")
print(f"\n>>> d(A,ref) = {dAr:.3f}%   d(B,ref) = {dBr:.3f}%")
print(f">>> d(A,B)   = {dAB:.3f}%   d(B,A)   = {dBA:.3f}%")
print(f">>> 样本间差异 / 样本-参考差异 = {((dAB+dBA)/2)/((dAr+dBr)/2):.2f}")
PY
