#!/usr/bin/env bash
# ts_gate.sh —— 一击定性 Ts/Tv 闸门（mawk 兼容版）
#
# 用现有 5 个 ~9x 样本联合 call，把 SNP 按「携带 alt 的样本数 / 位点深度 / QUAL」分层统计 Ts/Tv。
#   测序误差在每个样本里独立发生 -> 误差位点基本只出现在 1 个样本里
#   真变异会被多个样本独立共享
# 判据:
#   Ts/Tv 随 carriers 升高而升到 ~2.0  -> 门槛 1.8 合理，低值源自误差
#   Ts/Tv 升到 ~1.3 即平台           -> 该物种真实 Ts/Tv 就是 1.3，门槛设错了
#
# 用法: bash ts_gate.sh <BAM列表> [染色体数=8] [前缀=gate]
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
DATA=/home/hugo/data
REF=$DATA/ref/ref_GCF_023101765.2.fna
VAR=$DATA/04_variant
TMP=$DATA/tmp
LIST="${1:?需要 BAM 列表}"
NCHR="${2:-8}"
PREFIX="${3:-gate}"
OUT=$VAR/${PREFIX}.vcf.gz
LOG=$VAR/${PREFIX}.log
mkdir -p "$VAR" "$TMP"
log(){ printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "$LOG"; }

REG=$(sort -k2,2 -rn "${REF}.fai" | head -"$NCHR" | cut -f1 | paste -sd, -)
GLEN=$(sort -k2,2 -rn "${REF}.fai" | head -"$NCHR" | awk '{s+=$2} END{print s}')
log "区域: $NCHR 条最大染色体, 共 $((GLEN/1000000)) Mb"

mapfile -t BAMS < <(grep -v '^#' "$LIST" | grep -v '^$')
log "样本数=${#BAMS[@]}  列表: $LIST"

if [ ! -s "$OUT" ]; then
  log "mpileup+call 开始（这步最慢，耐心等）"
  bcftools mpileup -f "$REF" -a AD,DP -q 20 -Q 20 -d 500 -r "$REG" -Ou "${BAMS[@]}" 2>>"$LOG" \
    | bcftools call -m -v -a GQ -Oz -o "$OUT" 2>>"$LOG"
  log "mpileup rc=${PIPESTATUS[0]}"
else
  log "VCF 已存在，跳过 call"
fi
bcftools index -f -t "$OUT" 2>>"$LOG"
NREC=$(bcftools view -H "$OUT" 2>/dev/null | wc -l)
log "原始记录数=$NREC"
if [ "$NREC" -eq 0 ]; then log "[FATAL] 无记录，终止"; exit 1; fi

TAB=$TMP/${PREFIX}.tab
bcftools query -f '%CHROM\t%POS\t%REF\t%ALT\t%QUAL\t%INFO/DP[\t%GT]\n' "$OUT" > "$TAB"
NROW=$(wc -l < "$TAB")
NS=$(head -1 "$TAB" | awk -F'\t' '{print NF-6}')
log "导出 $TAB ($NROW 行, 6+${NS} 列, 即 ${NS} 个样本)"

echo
echo "===================== 分层 Ts/Tv ====================="
awk -F'\t' -v NS="$NS" '
function ists(r,a){ return ((r=="A"&&a=="G")||(r=="G"&&a=="A")||(r=="C"&&a=="T")||(r=="T"&&a=="C")) }
function reg(k,ist){ N[k]++; if(ist) TS[k]++; else TV[k]++ }
{
  ref=$3; alt=$4; q=$5+0; dp=$6+0
  if(length(ref)!=1 || length(alt)!=1) next
  if(ref==alt) next
  ac=0; car=0
  for(i=7;i<=NF;i++){
    g=$i; if(g=="" || g==".") continue
    gsub(/\|/,"/",g)
    if(g ~ /\//){
      n=split(g,a,"/"); has=0
      for(j=1;j<=n;j++){ if(a[j]==".") continue; if(a[j]!="0"){ ac++; has=1 } }
      if(has) car++
    } else { if(g!="0"){ ac++; car++ } }
  }
  if(ac==0) next
  ist=ists(ref,alt)
  reg("ALL",ist)
  if(ac==1) reg("AC1",ist); else if(ac==2) reg("AC2",ist); else if(ac<=4) reg("AC3_4",ist); else reg("AC5p",ist)
  reg("CAR" car, ist)
  if(q<20) reg("Q_lt20",ist); else if(q<50) reg("Q_20_50",ist); else if(q<100) reg("Q_50_100",ist); else reg("Q_gt100",ist)
  if(dp<10) reg("DP_lt10",ist); else if(dp<20) reg("DP_10_20",ist); else if(dp<45) reg("DP_20_45",ist); else if(dp<90) reg("DP_45_90",ist); else reg("DP_gt90",ist)
  if(q>50 && car>=2) reg("STRICT_Q50_CAR2",ist)
  if(q>100 && car>=3) reg("STRICT_Q100_CAR3",ist)
  tot++
}
function line(k,label,  n1,v1){
  n1=N[k]+0; v1=TV[k]+0
  printf "  %-18s n=%-10d  Ts=%-10d Tv=%-10d  Ts/Tv=%s\n", label, n1, TS[k]+0, v1, (v1>0? sprintf("%.3f",(TS[k]+0)/v1) : "NA")
}
END{
  printf "  总位点(有alt)=%d\n\n", tot
  print "--- 总体 ---"
  line("ALL","ALL")
  print "--- 按等位计数 AC ---"
  line("AC1","AC=1"); line("AC2","AC=2"); line("AC3_4","AC=3-4"); line("AC5p","AC>=5")
  print "--- 按携带alt的样本数 carriers ---"
  for(i=1;i<=5;i++) line("CAR" i, "carriers=" i)
  print "--- 按 QUAL ---"
  line("Q_lt20","Q<20"); line("Q_20_50","Q20-50"); line("Q_50_100","Q50-100"); line("Q_gt100","Q>100")
  print "--- 按位点总深度 DP ---"
  line("DP_lt10","DP<10"); line("DP_10_20","DP10-20"); line("DP_20_45","DP20-45"); line("DP_45_90","DP45-90"); line("DP_gt90","DP>90")
  print "--- 组合严格过滤 ---"
  line("STRICT_Q50_CAR2","Q>50 & car>=2")
  line("STRICT_Q100_CAR3","Q>100 & car>=3")
}
' "$TAB"

echo
echo "===================== 基因型构成 ====================="
awk -F'\t' '{for(i=7;i<=NF;i++){g=$i; if(g!="" && g!=".") print g}}' "$TAB" | sed 's/|/\//g' \
  | sort | uniq -c | sort -rn | head -10
echo
log "完成 -> $OUT"
