#!/usr/bin/env bash
# diag5.sh —— 决定性实验：变异位点的等位基因支持率（真实分化 vs 随机错误）
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
R=/home/hugo/data/ref/ref_GCF_023101765.2.fna
TMPD=/home/hugo/data/tmp
RGN=NC_064236.1:5000000-5300000

mkdir -p "$TMPD"
echo "区域 $RGN （单样本 SRR11528382）"
bcftools mpileup -f "$R" -a AD -q 20 -Q 20 -r "$RGN" \
  /home/hugo/data/03_align/SRR11528382.dedup.bam -Ou 2>/dev/null \
  | bcftools call -m -v -Oz -o "${TMPD}/diag5.vcf.gz" 2>/dev/null
bcftools index -t "${TMPD}/diag5.vcf.gz" 2>/dev/null

echo
echo "=== 前 25 个位点的 REF/ALT/深度（AD = 参考等位深度,变体深度）==="
bcftools query -f '%POS\t%REF\t%ALT[\t%AD]\n' "${TMPD}/diag5.vcf.gz" 2>/dev/null | head -25

echo
echo "=== 变体支持率分布（alt/(ref+alt) 直方图）==="
bcftools query -f '[\t%AD]\n' "${TMPD}/diag5.vcf.gz" 2>/dev/null \
  | awk -F'\t' '{
      for(i=2;i<=NF;i++){
        split($i,a,","); r=a[1]+0; alt=0
        for(j=2;j<=length(a);j++) alt+=a[j]
        tot=r+alt; if(tot<5) next
        f=alt/tot; b=int(f*10)/10; h[b]++; n++
      }
    } END{
      printf "  有效位点-样本对 = %d\n", n
      for(k in h) printf "%.1f\t%d\n", k, h[k]
    }' | sort -g \
  | awk '{printf "  支持率 %4.1f : %-60s %d\n", $1, substr("############################################################", 1, int($2/ (1+$2) *50 )+1), $2}'

echo
echo "=== 结论性指标 ==="
bcftools query -f '[\t%AD]\n' "${TMPD}/diag5.vcf.gz" 2>/dev/null | awk -F'\t' '
{
  for(i=2;i<=NF;i++){
    split($i,a,","); r=a[1]+0; alt=0
    for(j=2;j<=length(a);j++) alt+=a[j]
    tot=r+alt; if(tot<5) next
    f=alt/tot; n++
    if(f>=0.9) hi++; else if(f>=0.7) mid++; else if(f>=0.3) het++; else lo++
  }
} END{
  printf "  支持率 >=90%%（疑似真实纯合分化）: %d (%.1f%%)\n", hi, 100*hi/n
  printf "  支持率 70-90%%                    : %d (%.1f%%)\n", mid, 100*mid/n
  printf "  支持率 30-70%%（疑似杂合）        : %d (%.1f%%)\n", het, 100*het/n
  printf "  支持率 <30%%（疑似噪音/错误）     : %d (%.1f%%)\n", lo, 100*lo/n
  printf "  合计 = %d\n", n
}'
