#!/usr/bin/env bash
# tune2.sh —— 验证假阳性是否来自 indel 附近（bwa 无局部重比对的典型症状）
set -u
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
eval "$("$MM" shell hook -s bash)"
micromamba activate sfru

VAR=/mnt/c/SF_data/04_variant
RAW=${VAR}/pilot_0915_raw.vcf.gz
FAI=/mnt/c/SF_data/03_align/ref_GCF_023101765.2.fna.fai
awk '$2>1000000{print $1}' "$FAI" > /tmp/chroms.txt

tstv() {
  bcftools view -H -m2 -M2 -v snps "$1" 2>/dev/null \
  | awk -F'\t' '{r=$4;a=$5;
      if((r=="A"&&a=="G")||(r=="G"&&a=="A")||(r=="C"&&a=="T")||(r=="T"&&a=="C")) ts++;
      else if(length(r)==1&&length(a)==1) tv++}
    END{if(ts+tv==0) print "NA"; else printf "%.2f (%d 位点)", ts/tv, ts+tv}'
}

printf "%-56s %s\n" "处理" "Ts/Tv"
printf "%s\n" "----------------------------------------------------------------------"

# 基线
bcftools filter -i 'QUAL>100 && INFO/DP>=5 && INFO/DP<=40' -Ou "$RAW" 2>/dev/null \
 | bcftools view -m2 -M2 -Oz -o /tmp/base.vcf.gz 2>/dev/null
bcftools index -t -f /tmp/base.vcf.gz
printf "%-56s %s\n" "基线 QUAL>100 + DP5~40" "$(tstv /tmp/base.vcf.gz)"

# SnpGap：剔除 indel 附近 N bp 内的 SNP
for g in 3 5 10 20; do
  bcftools filter -g $g -Oz -o /tmp/gap$g.vcf.gz /tmp/base.vcf.gz 2>/dev/null
  bcftools index -t -f /tmp/gap$g.vcf.gz
  printf "%-56s %s\n" "  + 剔除 indel ${g}bp 内的 SNP" "$(tstv /tmp/gap$g.vcf.gz)"
done

echo
echo "--- 再叠加"仅保留 31 条主染色体" ---"
for g in 5 10; do
  bcftools view -T /tmp/chroms.txt -Oz -o /tmp/chr_gap$g.vcf.gz /tmp/gap$g.vcf.gz 2>/dev/null
  bcftools index -t -f /tmp/chr_gap$g.vcf.gz
  printf "%-56s %s\n" "  + 主染色体 (gap=$g)" "$(tstv /tmp/chr_gap$g.vcf.gz)"
done

echo
echo "--- 再叠加杂合子等位平衡过滤（AD 比例 0.25~0.75）---"
bcftools view -T /tmp/chroms.txt -Ou /tmp/gap10.vcf.gz 2>/dev/null \
 | bcftools filter -i 'QUAL>150' -Oz -o /tmp/final.vcf.gz 2>/dev/null
bcftools index -t -f /tmp/final.vcf.gz
printf "%-56s %s\n" "  + 主染色体 + QUAL>150" "$(tstv /tmp/final.vcf.gz)"
