#!/usr/bin/env bash
set -u
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
eval "$("$MM" shell hook -s bash)"
micromamba activate sfru
RAW=/mnt/c/SF_data/04_variant/pilot_0915_raw.vcf.gz
echo "=== A. 覆盖深度分布（原始 callset，看重复区塌陷程度）==="
bcftools query -f '%INFO/DP\n' "$RAW" 2>/dev/null | awk '
  {d++; s+=$1; if($1<=15)a++; else if($1<=40)b++; else if($1<=100)c++; else if($1<=1000)e++; else f++}
  END{printf "  平均DP %.1f | ≤15: %.1f%% | 16-40: %.1f%% | 41-100: %.1f%% | 101-1000: %.1f%% | >1000: %.1f%%\n",
      s/d, a/d*100, b/d*100, c/d*100, e/d*100, f/d*100}'
echo "=== B. 杂合率与等位平衡（QUAL>100, DP 5~40, 双等位 SNP）==="
bcftools filter -i 'QUAL>100 && INFO/DP>=5 && INFO/DP<=40' -Ou "$RAW" 2>/dev/null \
 | bcftools view -m2 -M2 -v snps -Ou 2>/dev/null \
 | bcftools query -f '[%GT\t%{AD}\t%DP]\n' 2>/dev/null \
 | awk -F'\t' '{
     for(i=1;i<=NF;i+=3){
       g=$i; ad=$(i+1); dp=$(i+2)+0;
       split(ad, a, ",");
       tot=a[1]+a[2]; if(tot==0) continue;
       if(g=="0/1"||g=="0|1"){ het++; ab+=a[2]/tot }
       else if(g=="1/1"||g=="1|1") homalt++;
       else if(g=="0/0"||g=="0|0") homref++;
       n++
     }}
   END{printf "  纯合参考 %d (%.1f%%)\n  杂合     %d (%.1f%%)\n  纯合变异 %d (%.1f%%)\n  杂合子平均等位平衡 %.3f（真杂合应≈0.5）\n",
       homref, homref/n*100, het, het/n*100, homalt, homalt/n*100, ab/het}'
