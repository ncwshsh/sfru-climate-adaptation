#!/usr/bin/env bash
# diag6.sh —— 波多黎各 vs 浙江：谁偏离参考？
# 若"两样本共同变体"占多数 -> 参考偏离群体；若"一个变一个不变"占多数 -> 样本间分化
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
R=/home/hugo/data/ref/ref_GCF_023101765.2.fna
TMPD=/home/hugo/data/tmp
RGN=NC_064236.1:5000000-5300000
A=/home/hugo/data/03_align/SRR10980085.dedup.bam   # 波多黎各
B=/home/hugo/data/03_align/SRR11528382.dedup.bam   # 浙江
mkdir -p "$TMPD"

echo "区域 $RGN   样本: 波多黎各(SRR10980085) vs 浙江(SRR11528382)"
bcftools mpileup -f "$R" -a AD -q 20 -Q 20 -r "$RGN" "$A" "$B" -Ou 2>/dev/null \
  | bcftools call -m -v -Oz -o "${TMPD}/two.vcf.gz" 2>/dev/null
bcftools index -t "${TMPD}/two.vcf.gz" 2>/dev/null

echo
echo "=== 变异位点上两样本的基因型组合（前 20 种）==="
echo "列序: 波多黎各 浙江   计数"
bcftools query -f '[%GT\t%GT]\n' "${TMPD}/two.vcf.gz" 2>/dev/null \
  | awk -F'\t' '{print $1" "$2}' | sort | uniq -c | sort -rn | head -20

echo
echo "=== 归类 ==="
bcftools query -f '[%GT\t%GT]\n' "${TMPD}/two.vcf.gz" 2>/dev/null | awk -F'\t' '
{
  a=$1; b=$2
  if (a=="0/0" && b=="0/0") both0++;
  else if (a!="0/0" && a!="./." && b!="0/0" && b!="./.") bothv++;
  else if (a=="./." || b=="./.") miss++;
  else onev++;
  n++
}
END{
  printf "  两样本都 == 0/0   : %8d (%.1f%%)\n", both0, 100*both0/n
  printf "  两样本都 != 0/0   : %8d (%.1f%%)\n", bothv, 100*bothv/n
  printf "  一个变异一个不变  : %8d (%.1f%%)\n", onev, 100*onev/n
  printf "  含缺失基因型      : %8d (%.1f%%)\n", miss, 100*miss/n
  printf "  合计              : %8d\n", n
}'

echo
echo "=== 两样本各自的 Alt 支持率（看是否为纯合）==="
bcftools query -f '[\t%AD]\n' "${TMPD}/two.vcf.gz" 2>/dev/null | awk -F'\t' '
{
  for(i=2;i<=NF;i++){
    split($i,a,","); r=a[1]+0; alt=0
    for(j=2;j<=length(a);j++) alt+=a[j]
    tot=r+alt; if(tot<5) next
    f=alt/tot
    tag=(i==2?"波多黎各":"浙江")
    cnt[tag]++
    if(f>=0.9) hi[tag]++
  }
} END{ for(t in cnt) printf "  %-8s 有效位点 %6d  其中 alt>=90%%: %6d (%.1f%%)\n", t, cnt[t], hi[t]+0, 100*hi[t]/cnt[t] }'
