#!/usr/bin/env bash
set -u
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
eval "$("$MM" shell hook -s bash)"
micromamba activate sfru
RAW=/mnt/c/SF_data/04_variant/pilot_0915_raw.vcf.gz
echo "=== VCF 中 REF 是否含小写（软掩码）==="
bcftools query -f '%REF\n' "$RAW" 2>/dev/null | awk '{if($0 ~ /[acgt]/) lo++; else up++} END{printf "  小写 REF: %d\n  大写 REF: %d\n", lo, up}'
echo "=== 参考基因组是否软掩码 ==="
zcat /mnt/c/SF_data/00_ref/GCF_023101765.2_genomic.fna.gz 2>/dev/null | head -100000 | grep -v '^>' | tr -d '\n' | fold -w1 | sort -u | tr '\n' ' ' | head -c 300
echo
echo "=== 重新计算 Ts/Tv（先统一转大写）==="
bcftools view -H -m2 -M2 -v snps "$RAW" 2>/dev/null | awk -F'\t' '{
  r=toupper($4); a=toupper($5);
  if(length(r)!=1||length(a)!=1) next;
  if((r=="A"&&a=="G")||(r=="G"&&a=="A")||(r=="C"&&a=="T")||(r=="T"&&a=="C")) ts++; else tv++}
  END{printf "  全部位点   Ts/Tv = %.2f  (ts=%d tv=%d)\n", ts/tv, ts, tv}'
bcftools filter -i 'QUAL>100 && INFO/DP>=5 && INFO/DP<=40' -Ou "$RAW" 2>/dev/null | bcftools view -H -m2 -M2 -v snps 2>/dev/null | awk -F'\t' '{
  r=toupper($4); a=toupper($5);
  if(length(r)!=1||length(a)!=1) next;
  if((r=="A"&&a=="G")||(r=="G"&&a=="A")||(r=="C"&&a=="T")||(r=="T"&&a=="C")) ts++; else tv++}
  END{printf "  QUAL>100+DP5~40 Ts/Tv = %.2f  (ts=%d tv=%d)\n", ts/tv, ts, tv}'
