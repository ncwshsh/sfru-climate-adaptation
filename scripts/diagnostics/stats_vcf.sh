#!/usr/bin/env bash
# stats_vcf.sh —— 对任意 VCF 输出核心质控指标（Ts/Tv、SNP 数、基因型构成）
# 用法: bash stats_vcf.sh <vcf.gz> [可选: 区域]
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
R=/home/hugo/data/ref/ref_GCF_023101765.2.fna
V=${1:?需要 VCF 路径}
RGN=${2:-}

echo "===== $V ====="
if [ -n "$RGN" ]; then
  bcftools view -r "$RGN" -Oz -o /tmp/_sub.vcf.gz "$V" 2>/dev/null && V=/tmp/_sub.vcf.gz
fi
bcftools stats -F "$R" "$V" 2>/dev/null | grep -E '^SN|^TSTV'

echo "--- 基因型构成 ---"
bcftools query -f '[%GT ]\n' "$V" 2>/dev/null \
  | tr ' ' '\n' | grep -v '^$' | sort | uniq -c | sort -rn | head -8

echo "--- 深度分布（前 1 万位点）---"
bcftools query -f '%DP\n' "$V" 2>/dev/null | head -10000 | sort -n \
  | awk '{a[NR]=$1} END{print "  min="a[1]"  p25="a[int(NR*0.25)]"  中位="a[int(NR*0.5)]"  p75="a[int(NR*0.75)]"  max="a[NR]"  n="NR}'
