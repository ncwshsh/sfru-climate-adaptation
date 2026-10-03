#!/usr/bin/env bash
set -u
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
eval "$("$MM" shell hook -s bash)"
micromamba activate sfru
RAW=/mnt/c/SF_data/04_variant/pilot_0915_raw.vcf.gz
echo "=== 基因型构成（QUAL>100, DP 5~40, 双等位 SNP）==="
bcftools filter -i 'QUAL>100 && INFO/DP>=5 && INFO/DP<=40' -Ou "$RAW" 2>/dev/null \
 | bcftools view -m2 -M2 -v snps -Ou 2>/dev/null \
 | bcftools query -f '[%GT|]\n' 2>/dev/null \
 | tr '|' '\n' | grep -v '^$' | sort | uniq -c | sort -rn | head -8
echo
echo "=== 各位点两样本基因型组合（看是否多为单例）==="
bcftools filter -i 'QUAL>100 && INFO/DP>=5 && INFO/DP<=40' -Ou "$RAW" 2>/dev/null \
 | bcftools view -m2 -M2 -v snps -Ou 2>/dev/null \
 | bcftools query -f '[%GT ]\n' 2>/dev/null \
 | awk '{if($1=="0/0"&&$2=="0/0")cc++; else if($1==$2)shared++; else private++}
   END{printf "  两样本均为纯合参考: %d\n  两样本基因型相同  : %d\n  两样本基因型不同  : %d (单例/差异位点)\n", cc, shared, private}'
