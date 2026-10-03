#!/bin/bash
# 读段级诊断: NM 分布是否单峰(均匀分歧) / 双峰(混合成分)
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
set -u
REF=/home/hugo/data/ref/ref_GCF_023101765.2.fna
S=SRR11528381
BAM=/home/hugo/data/03_align/${S}.dedup.bam
REG=NC_064212.1:1-5000000

echo "############ 1. 读段长度分布 ############"
samtools view "$BAM" "$REG" | head -50000 | awk '{print length($10)}' | sort -n | uniq -c | sort -rn | head -5

echo
echo "############ 2. NM 直方图 (全部读段) ############"
samtools view "$BAM" "$REG" | head -300000 \
 | awk '{for(i=12;i<=NF;i++) if($i ~ /^NM:i:/){split($i,a,":"); print a[3]; break}}' \
 | sort -n | uniq -c | awk '{printf "NM=%-3s  %8d  %s\n", $2, $1, ($2==0?"<-- 完全一致":($2>=15?"<-- 高分歧":""))}'
echo "--- 统计 ---"
samtools view "$BAM" "$REG" | head -300000 \
 | awk '{for(i=12;i<=NF;i++) if($i ~ /^NM:i:/){split($i,a,":"); n++; s+=a[3]; if(a[3]==0)z++; break}} END{printf "n=%d  平均NM=%.3f  NM==0占比=%.1f%%\n", n, s/n, 100*z/n}'

echo
echo "############ 3. NM 分布 (MAPQ>=40) ############"
samtools view -q 40 "$BAM" "$REG" | head -300000 \
 | awk '{for(i=12;i<=NF;i++) if($i ~ /^NM:i:/){split($i,a,":"); n++; s+=a[3]; if(a[3]==0)z++; c[a[3]]++; break}} END{printf "n=%d  平均NM=%.3f  NM==0占比=%.1f%%\n", n, s/n, 100*z/n}'

echo
echo "############ 4. NM 分布 (CIGAR 纯 M, 无 indel/softclip, MAPQ>=40) ############"
samtools view -q 40 "$BAM" "$REG" | awk '$6 ~ /^[0-9]+M$/' | head -300000 \
 | awk '{for(i=12;i<=NF;i++) if($i ~ /^NM:i:/){split($i,a,":"); n++; s+=a[3]; if(a[3]==0)z++; if(a[3]<=1)o++; break}} END{printf "n=%d  平均NM=%.3f  NM==0占比=%.1f%%  NM<=1占比=%.1f%%\n", n, s/n, 100*z/n, 100*o/n}'

echo
echo "############ 5. MAPQ 分布 ############"
samtools view "$BAM" "$REG" | head -300000 | awk '{m=$5; if(m>=60)b[">=60"]++; else if(m>=40)b["40-59"]++; else if(m>=20)b["20-39"]++; else if(m>=1)b["1-19"]++; else b["0"]++} END{for(k in b) printf "MAPQ %-6s %8d\n", k, b[k]}'

echo
echo "############ 6. 干净读段(MAPQ>=40,纯M)的 k-mer 包含率 ############"
samtools view -q 40 "$BAM" NC_064212.1:1-3000000 | awk '$6 ~ /^[0-9]+M$/' \
 | awk 'BEGIN{OFS="\n"} {print ">r"NR; print $10}' | head -600000 > /tmp/clean_reads.fa
echo "干净 reads = $(grep -c '^>' /tmp/clean_reads.fa)"
samtools faidx "$REF" NC_064212.1:1-3000000 > /tmp/ref_reg.fa

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
ref=''.join(rf('/tmp/ref_reg.fa'))
rs=set(kh(ref))
tot=hit=0
for i,s in enumerate(rf('/tmp/clean_reads.fa')):
    if i>=150000: break
    for h in kh(s):
        tot+=1
        if h in rs: hit+=1
c=hit/tot
print(f"干净读段 k-mer 包含率 = {c:.4f}  ->  d_est = {(1-c**(1.0/K))*100:.3f}%")
# 校准: 3% 分歧的模拟读段应给出多少包含率
import random
random.seed(1)
nsim=20000; tb=hb=0
bases='ACGT'
for i in range(nsim):
    st=random.randrange(0,len(ref)-150)
    s=list(ref[st:st+150])
    for j in range(len(s)):
        if random.random()<0.03: s[j]=random.choice(bases)
    for h in kh(''.join(s)):
        tb+=1
        if h in rs: hb+=1
print(f"[校准] 模拟 3% 分歧读段 包含率 = {hb/tb:.4f}  (理论 {(0.97**K):.4f})")
PY
