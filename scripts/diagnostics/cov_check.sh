#!/usr/bin/env bash
# cov_check.sh —— 查 BAM 的真实覆盖分布（区分「有效深度不足」与「覆盖极度不均」）
# 用法: bash cov_check.sh <BAM> [前缀]
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
BAM="${1:?需要 BAM}"
P="${2:-cov}"
REF=/home/hugo/data/ref/ref_GCF_023101765.2.fna
TMP=/home/hugo/data/tmp

echo "=== flagstat ==="
samtools flagstat -@ 4 "$BAM" | grep -E 'in total|primary mapped \(|primary duplicates|secondary|supplementary'

echo
echo "=== idxstats 汇总 ==="
samtools idxstats "$BAM" | awk '
  {m+=$3; u+=$4; len+=$2}
  END{ printf "参考总长=%d bp\n比对上=%d\n未比对=%d\n全库均值深度(含重复)=%.2f x\n", len,m,u,m*151/len }'

echo
echo "=== 去重后有效深度（按 flag 0x400 扣除）==="
tot=$(samtools view -c -F 0x904 "$BAM" 2>/dev/null)
nd=$(samtools view -c -F 0x904 -G 0x400 "$BAM" 2>/dev/null)
awk -v t="$tot" -v n="$nd" 'BEGIN{ printf "非次级比对上=%d  其中非重复=%d (%.1f%%)\n去重后有效深度=%.2f x\n", t, n, 100*n/t, n*151/383923118 }'

echo
echo "=== samtools coverage（前 8 大染色体）==="
REG=$(sort -k2,2 -rn "${REF}.fai" | head -8 | cut -f1 | paste -sd' ' -)
samtools coverage -r "$REG" "$BAM" 2>/dev/null | awk 'NR==1||NR>1{print}'

echo
echo "=== 实测深度直方图（最大染色体 NC_064212.1 全条）==="
CHR=$(sort -k2,2 -rn "${REF}.fai" | head -1 | cut -f1)
CLEN=$(sort -k2,2 -rn "${REF}.fai" | head -1 | cut -f2)
echo "染色体 $CHR ($CLEN bp)"
samtools depth -a -r "$CHR" -Q 20 -q 20 "$BAM" 2>/dev/null | awk '
  { d=$3; n++; s+=d; if(d==0) z++; if(d>=1) c1++; if(d>=5)c5++; if(d>=10)c10++; if(d>=20)c20++; if(d>=30)c30++
    b = (d<1)?0 : (d<3)?1 : (d<5)?2 : (d<10)?3 : (d<15)?4 : (d<20)?5 : (d<25)?6 : (d<30)?7 : (d<40)?8 : (d<60)?9 : 10
    H[b]++ }
  END{
    printf "位点数=%d  均值=%.2f x\n", n, s/n
    printf "深度0占比=%.1f%%  >=1x:%.1f%%  >=5x:%.1f%%  >=10x:%.1f%%  >=20x:%.1f%%  >=30x:%.1f%%\n", 100*z/n,100*c1/n,100*c5/n,100*c10/n,100*c20/n,100*c30/n
    lbl[0]="0x"; lbl[1]="1-2x"; lbl[2]="3-4x"; lbl[3]="5-9x"; lbl[4]="10-14x"; lbl[5]="15-19x"; lbl[6]="20-24x"; lbl[7]="25-29x"; lbl[8]="30-39x"; lbl[9]="40-59x"; lbl[10]=">=60x"
    for(i=0;i<=10;i++) printf "  %-8s %10d  %.1f%%  %s\n", lbl[i], H[i]+0, 100*(H[i]+0)/n, substr("##############################################################",1,int((H[i]+0)/n*150))
  }'
