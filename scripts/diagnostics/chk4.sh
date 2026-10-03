#!/usr/bin/env bash
set -u
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
eval "$("$MM" shell hook -s bash)"
micromamba activate sfru
RAW=/mnt/c/SF_data/04_variant/pilot_0915_raw.vcf.gz
echo "=== 各基因型类别的平均深度（低覆盖丢失等位基因 -> 纯合位点深度应更低）==="
bcftools filter -i 'QUAL>100 && INFO/DP>=5 && INFO/DP<=40' -Ou "$RAW" 2>/dev/null \
 | bcftools view -m2 -M2 -v snps -Ou 2>/dev/null \
 | bcftools query -f '%INFO/DP\t[%GT\t]\n' 2>/dev/null \
 | tr -d '\0' \
 | awk -F'\t' '{
     dp=$1+0
     for(i=2;i<=NF;i++){ g=$i; gsub(/ /,"",g);
       if(g=="1/1"){n11++; s11+=dp}
       else if(g=="0/1"){n01++; s01+=dp}
       else if(g=="0/0"){n00++; s00+=dp}
     }}
   END{printf "  0/0 纯合参考: %8d 个, 平均深度 %.2f\n  0/1 杂合    : %8d 个, 平均深度 %.2f\n  1/1 纯合变异: %8d 个, 平均深度 %.2f\n",
       n00, s00/n00, n01, s01/n01, n11, s11/n11}'
