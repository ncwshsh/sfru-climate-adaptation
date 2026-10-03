#!/usr/bin/env bash
# expB.sh —— 深度响应实验：同一个体 9x(单 lane) vs 18.3x(两 lane 合并)
# 合并两条独立 lane -> 深度翻倍。若 Ts/Tv 随深度显著上升 => 低 Ts/Tv 主因是测序误差
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
DATA=/home/hugo/data
REF=$DATA/ref/ref_GCF_023101765.2.fna
ALIGN=$DATA/03_align
VAR=$DATA/04_variant
LOG=$VAR/expB.log
mkdir -p "$VAR"
log(){ printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "$LOG"; }

MERGED=$ALIGN/CN_merged.dedup.bam
A=$ALIGN/SRR11528381.dedup.bam
B=$ALIGN/SRR11528382.dedup.bam

REG=$(sort -k2,2 -rn "${REF}.fai" | head -8 | cut -f1 | paste -sd, -)
GEN=$(awk '{s+=$2} END{print s}' "${REF}.fai")

if [ ! -s "$MERGED" ]; then
  log "合并两条 lane + 重新标记重复"
  samtools merge -@ 8 -f - "$A" "$B" 2>>"$LOG" \
    | samtools sort -@ 8 -m 2G -T $DATA/tmp/mrg -o $DATA/tmp/CN.mrg.sorted.bam - 2>>"$LOG"
  samtools markdup -@ 8 -r -s $DATA/tmp/CN.mrg.sorted.bam "$MERGED" 2>>"$LOG"
  samtools index -@ 8 "$MERGED"
  rm -f $DATA/tmp/CN.mrg.sorted.bam
fi

echo "===== 合并后深度 ====="
for b in "$MERGED" "$A" "$B"; do
  n=$(basename "$b" .dedup.bam)
  r=$(samtools idxstats "$b" 2>/dev/null | awk '{s+=$3} END{print s}')
  L=$(samtools view "$b" 2>/dev/null | head -20000 | awk '{s+=length($10);n++} END{if(n>0)printf "%.1f",s/n;else print 150}')
  awk -v n="$n" -v r="$r" -v L="$L" -v g="$GEN" 'BEGIN{printf "  %-24s mapped=%-12d avgLen=%-6s 深度=%.2fx\n", n, r, L, r*L/g}'
done

for tag in merged laneA; do
  if [ "$tag" = "merged" ]; then BAMS="$MERGED"; else BAMS="$A"; fi
  OUT=$VAR/expB_${tag}.vcf.gz
  [ -s "$OUT" ] && { log "$tag 已存在，跳过"; continue; }
  log "[$tag] mpileup+call"
  bcftools mpileup -f "$REF" -a AD,DP -q 20 -Q 20 -d 800 -r "$REG" -Ou "$BAMS" 2>>"$LOG" \
    | bcftools call -m -v -a GQ -Oz -o "$OUT" 2>>"$LOG"
  bcftools index -f -t "$OUT"
  log "[$tag] 记录数=$(bcftools view -H "$OUT" | wc -l)"
done

echo
echo "========== 对比：Ts/Tv 随深度 =========="
printf "%-10s %12s %12s %12s %10s\n" "样本" "SNP数" "Ts" "Tv" "Ts/Tv"
for tag in laneA merged; do
  st=$(bcftools stats -F "$REF" $VAR/expB_${tag}.vcf.gz 2>/dev/null)
  n=$(printf '%s' "$st" | awk -F'\t' '/^SN/{if($3 ~ /number of SNPs/){print $4}}')
  ts=$(printf '%s' "$st" | awk -F'\t' '/^TSTV/{print $3; exit}')
  tv=$(printf '%s' "$st" | awk -F'\t' '/^TSTV/{print $4; exit}')
  ratio=$(printf '%s' "$st" | awk -F'\t' '/^TSTV/{print $5; exit}')
  printf "%-10s %12s %12s %12s %10s\n" "$tag" "$n" "$ts" "$tv" "$ratio"
done

echo
echo "========== 合并样本：按位点深度分层的 Ts/Tv =========="
TAB=$DATA/tmp/expB.tab
bcftools query -f '%REF\t%ALT\t%QUAL\t%INFO/DP\n' $VAR/expB_merged.vcf.gz > "$TAB"
awk -F'\t' '
function ists(r,a){ return ((r=="A"&&a=="G")||(r=="G"&&a=="A")||(r=="C"&&a=="T")||(r=="T"&&a=="C")) }
{
  r=$1;a=$2;q=$3+0;dp=$4+0
  if(length(r)!=1||length(a)!=1||r==a) next
  ist=ists(r,a)
  if(dp<8) k="DP_lt8"; else if(dp<15) k="DP_8_15"; else if(dp<25) k="DP_15_25"; else if(dp<40) k="DP_25_40"; else k="DP_gt40"
  N[k]++; if(ist) TS[k]++; else TV[k]++
  N["ALL"]++; if(ist) TS["ALL"]++; else TV["ALL"]++
}
END{
  split("ALL DP_lt8 DP_8_15 DP_15_25 DP_25_40 DP_gt40", o, " ")
  for(i=1;i<=6;i++){ k=o[i]; v=TV[k]+0; printf "  %-10s n=%-9d Ts=%-9d Tv=%-9d Ts/Tv=%s\n", k, N[k]+0, TS[k]+0, v, (v>0?sprintf("%.3f",(TS[k]+0)/v):"NA") }
}
' "$TAB"
log "expB 完成"
