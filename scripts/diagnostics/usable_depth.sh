#!/usr/bin/env bash
# usable_depth.sh —— 31 条染色体的「可用深度」（-q20 -Q20 过滤后）vs raw 深度
# 意义：mpileup 用的就是 -q20 -Q20，所以可用深度才是变异检测的分子
# 用法: bash usable_depth.sh <BAM>
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
BAM="${1:?需要 BAM}"
REF=/home/hugo/data/ref/ref_GCF_023101765.2.fna

CHRS=$(awk '$2>1000000 {print $1}' "${REF}.fai" | paste -sd, -)
NCH=$(awk '$2>1000000' "${REF}.fai" | wc -l)
CHLEN=$(awk '$2>1000000 {s+=$2} END{print s}' "${REF}.fai")
echo "染色体条数=$NCH  总长=$CHLEN bp"

echo
echo "=== raw 深度（idxstats，含低质量/重复读）==="
samtools idxstats "$BAM" | awk -v L="$CHLEN" '$2>1000000 {m+=$3} END{printf "reads=%d  raw深度=%.2f x\n", m, m*151/L}'

echo
echo "=== 可用深度（samtools coverage -q 20 -Q 20，逐条）==="
samtools coverage -q 20 -Q 20 "$BAM" 2>/dev/null | awk 'NR==1 || $2>1000000' > /tmp/_cov.txt
head -1 /tmp/_cov.txt
echo "---- 全部 31 条染色体 ----"
tail -n +2 /tmp/_cov.txt

echo
echo "=== 加权汇总 ==="
awk 'NR>1 {num+=$7*$3; den+=$3; cov+=$3*$5/100; tot+=$3}
     END{ printf "可用加权均值深度 = %.2f x\n被覆盖>=1x碱基 = %.1f%%\n", num/den, 100*cov/tot }' /tmp/_cov.txt

echo
echo "=== 与 mpileup 实际用到的深度对照（VCF INFO/DP 中位数）==="
for v in /home/hugo/data/04_variant/kenya_22x.vcf.gz; do
  [ -s "$v" ] && bcftools query -f '%INFO/DP\n' "$v" 2>/dev/null | sort -n | awk -v n="$v" '
    {a[NR]=$1; s+=$1} END{ printf "%s\n  位点数=%d  DP中位数=%d  DP均值=%.1f\n", n, NR, a[int(NR/2)+1], s/NR }'
done
rm -f /tmp/_cov.txt
