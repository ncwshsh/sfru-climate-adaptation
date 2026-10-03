#!/usr/bin/env bash
# qc_vcf.sh —— pilot VCF 质量核验（WSL 内运行）
set -u
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
eval "$("$MM" shell hook -s bash)"
micromamba activate sfru

VAR=/mnt/c/SF_data/04_variant
RAW=${VAR}/pilot_0915_raw.vcf.gz
FLT=${VAR}/pilot_0915_raw_flt.vcf.gz

echo "########## 产物清单 ##########"
ls -lh ${VAR}/

echo
echo "########## 原始 VCF 总览 ##########"
grep "^SN" ${VAR}/pilot_0915_raw.stats | sed 's/^SN\t//' | awk -F'\t' '{printf "  %-42s %s\n", $2, $3}'

echo
echo "########## 转换/颠换比 (Ts/Tv) ##########"
grep "^TSTV" ${VAR}/pilot_0915_raw.stats | awk -F'\t' '{printf "  ts=%s  tv=%s  Ts/Tv=%s\n", $3, $4, $5}'

echo
echo "########## 过滤后 VCF ##########"
echo -n "  位点总数        : "; bcftools view -H "$FLT" | wc -l
echo -n "  仅 SNP          : "; bcftools view -H -v snps "$FLT" | wc -l
echo -n "  仅 INDEL        : "; bcftools view -H -v indels "$FLT" | wc -l
echo -n "  双样本均有基因型: "; bcftools view -H -i 'N_MISSING=0' "$FLT" | wc -l
echo -n "  仅 1 样本缺失   : "; bcftools view -H -i 'N_MISSING=1' "$FLT" | wc -l

echo
echo "########## 逐样本统计 ##########"
printf "  %-16s %10s %10s %10s %8s\n" "样本" "位点数" "纯合" "杂合" "杂合率"
for s in $(bcftools query -l "$FLT"); do
  tot=$(bcftools view -H -s "$s" -i "GT[@0]='hom' || GT[@0]='het'" "$FLT" 2>/dev/null | wc -l)
  hom=$(bcftools view -H -s "$s" -i "GT[@0]='hom'" "$FLT" 2>/dev/null | wc -l)
  het=$(bcftools view -H -s "$s" -i "GT[@0]='het'" "$FLT" 2>/dev/null | wc -l)
  if [ "$tot" -gt 0 ]; then
    rate=$(awk -v h="$het" -v t="$tot" 'BEGIN{printf "%.1f%%", h/t*100}')
  else
    rate="NA"
  fi
  printf "  %-16s %10s %10s %10s %8s\n" "$s" "$tot" "$hom" "$het" "$rate"
done

echo
echo "########## 深度分布（过滤后位点）##########"
bcftools query -f '[%DP]\n' "$FLT" 2>/dev/null | sort -n | awk '
  {a[NR]=$1; s+=$1}
  END{
    printf "  平均深度 %.1f  中位 %.0f  最小 %d  最大 %d  (n=%d)\n",
    s/NR, a[int(NR/2)], a[1], a[NR], NR
  }'

echo
echo "########## 前 12 条变异位点 ##########"
bcftools query -f '%CHROM:%POS\t%REF\t%ALT\t%QUAL[\t%GT]\n' "$FLT" 2>/dev/null | head -12
