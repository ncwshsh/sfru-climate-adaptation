#!/usr/bin/env bash
# ts_deep2.sh —— 单深样本 Ts/Tv 分层（v2：修正 het/hom 诊断的适用性）
#
# v1 的错误：拿「5 样本联合 VCF 的 het/hom 基线 0.351」去比「单样本 VCF 的 het/hom」。
#   联合 VCF 里一个位点上另有 4 个样本是 0/0，单样本 VCF 没有这些 0/0 -> 分母定义不同，不可比。
# v2 的正确做法：塌缩重复的诊断必须**在同一次分析内部**做——
#   比较「中深度档」与「高深度档」的 het/hom。旁系同源堆叠会让高深度档的假杂合暴增。
#   若 het/hom 随 DP 单调上升 -> 高深度档的 Ts/Tv 是假象；
#   若 het/hom 基本持平   -> 该档 Ts/Tv 可信。
#
# 用法: bash ts_deep2.sh <BAM> <前缀> [染色体数=8] [线程=8]
#   （若 04_variant/<前缀>.vcf.gz 已存在则跳过 call，仅重分析）
#   REF=<参考路径> 可覆盖参考（默认全量；做 ref_chr A/B 时必给，
#   且必须与 BAM 比对时用的参考一致，否则区域坐标/等位基因错配）
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
DATA=/home/hugo/data
# 参考可覆盖：默认全量（向后兼容）；做 ref_chr A/B 时用
#   REF=/home/hugo/data/ref/ref_chr.fna bash ts_deep2.sh <BAM> <前缀> 8 8
# ⚠️ 必须用与 BAM 比对时同一个参考，否则区域坐标与等位基因都对不上。
REF="${REF:-$DATA/ref/ref_GCF_023101765.2.fna}"
VAR=$DATA/04_variant
TMP=$DATA/tmp
BAM="${1:?需要 BAM 路径}"
PREFIX="${2:?需要前缀}"
NCHR="${3:-8}"
THREADS="${4:-8}"
OUT=$VAR/${PREFIX}.vcf.gz
TAB=$TMP/${PREFIX}.tab
LOG=$VAR/${PREFIX}.v2.log
mkdir -p "$VAR" "$TMP"
log(){ printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "$LOG"; }

REG=$(sort -k2,2 -rn "${REF}.fai" | head -"$NCHR" | cut -f1 | paste -sd, -)
GLEN=$(sort -k2,2 -rn "${REF}.fai" | head -"$NCHR" | awk '{s+=$2} END{print s}')
log "样本=$BAM  区域=${NCHR}条最大染色体 $((GLEN/1000000))Mb  线程=$THREADS"
BYTES=$(stat -c%s "$BAM" 2>/dev/null || echo 0)
mapd=$(samtools idxstats "$BAM" 2>/dev/null | awk '{m+=$3} END{print m+0}')
log "BAM 大小=$((BYTES/1048576)) MB  比对上 reads=$mapd"

if [ ! -s "$OUT" ]; then
  log "mpileup+call（-d 1000）"
  bcftools mpileup -f "$REF" -a AD,ADF,ADR,DP,SP -q 20 -Q 20 -d 1000 -r "$REG" \
      -Ou "$BAM" 2>>"$LOG" \
    | bcftools call -m -v -a GQ -Oz --threads "$THREADS" -o "$OUT" 2>>"$LOG"
  log "mpileup rc=${PIPESTATUS[0]} call rc=${PIPESTATUS[1]}"
else
  log "VCF 已存在，跳过 call"
fi
bcftools index -f -t "$OUT" 2>>"$LOG"
NREC=$(bcftools view -H "$OUT" 2>/dev/null | wc -l)
log "原始记录数=$NREC"
[ "$NREC" -eq 0 ] && { log "[FATAL] 无记录"; exit 1; }

if [ ! -s "$TAB" ]; then
  bcftools query -f '%CHROM\t%POS\t%REF\t%ALT\t%QUAL\t%INFO/DP\t%INFO/MQ\t[%GT\t%AD\t%DP]\n' "$OUT" > "$TAB"
fi
log "分析 $TAB ($(wc -l < "$TAB") 行)"

echo
echo "############### Ts/Tv 分层 v2 —— $PREFIX ###############"
awk -F'\t' '
function ists(r,a){ return ((r=="A"&&a=="G")||(r=="G"&&a=="A")||(r=="C"&&a=="T")||(r=="T"&&a=="C")) }
function reg(k,ist,g){
  N[k]++
  if(ist) TS[k]++; else TV[k]++
  if(g=="0/1"||g=="1/0") HT[k]++
  else if(g=="1/1")     HM[k]++
}
{
  ref=$3; alt=$4; q=$5+0; mq=$7+0; gt=$8; ad=$9; dp=$10+0
  if(length(ref)!=1 || length(alt)!=1) next
  if(ref==alt || alt=="." || alt=="<*>") next
  n=split(ad,A,","); r=A[1]+0; v=A[2]+0; s=r+v
  if(s<=0) next
  af=v/s
  g=gt; gsub(/\|/,"/",g)
  ist=ists(ref,alt)
  reg("ALL",ist,g)
  if(g=="0/0") reg("GT_00",ist,g); tot00++
  if(dp<5)reg("DP_lt5",ist,g); else if(dp<10)reg("DP_5_10",ist,g); else if(dp<20)reg("DP_10_20",ist,g); else if(dp<30)reg("DP_20_30",ist,g); else if(dp<45)reg("DP_30_45",ist,g); else if(dp<60)reg("DP_45_60",ist,g); else if(dp<90)reg("DP_60_90",ist,g); else reg("DP_gt90",ist,g)
  if(af<0.1)reg("AF_lt10",ist,g); else if(af<0.3)reg("AF_10_30",ist,g); else if(af<0.45)reg("AF_30_45",ist,g); else if(af<0.65)reg("AF_45_65",ist,g); else if(af<0.85)reg("AF_65_85",ist,g); else reg("AF_gt85",ist,g)
  if(q<20)reg("Q_lt20",ist,g); else if(q<50)reg("Q_20_50",ist,g); else if(q<100)reg("Q_50_100",ist,g); else reg("Q_gt100",ist,g)
  if(mq<50)reg("MQ_lt50",ist,g); else if(mq<60)reg("MQ_50_60",ist,g); else reg("MQ_gt60",ist,g)
  if(q>=50 && mq>=50 && dp>=20 && af>=0.35 && af<=0.65) reg("CLEAN_het",ist,g)
  if(q>=50 && mq>=50 && dp>=20 && af>=0.90) reg("CLEAN_hom",ist,g)
  tot++
}
function line(k,label, n1,v1,h1,m1){
  n1=N[k]+0; v1=TV[k]+0; h1=HT[k]+0; m1=HM[k]+0
  printf "  %-14s n=%-9d Ts/Tv=%-7s het/hom=%-7s het=%-8d hom=%d\n", label, n1,
    (v1>0? sprintf("%.3f",(TS[k]+0)/v1):"NA"),
    (m1>0? sprintf("%.3f",h1/m1):"NA"), h1, m1
}
END{
  printf "  含alt位点=%d   0/0 记录=%d (%.1f%%)\n\n", tot, tot00+0, (tot>0?100*(tot00+0)/(tot+tot00):0)
  print "--- 总体 ---"; line("ALL","ALL")
  print "--- 按深度 DP  ※重点看 het/hom 是否随 DP 上升（上升=塌缩重复）---"
  line("DP_lt5","DP<5"); line("DP_5_10","DP5-10"); line("DP_10_20","DP10-20"); line("DP_20_30","DP20-30"); line("DP_30_45","DP30-45"); line("DP_45_60","DP45-60"); line("DP_60_90","DP60-90"); line("DP_gt90","DP>90")
  print "--- 按等位分数 AF ---"
  line("AF_lt10","AF<10%"); line("AF_10_30","AF10-30%"); line("AF_30_45","AF30-45%"); line("AF_45_65","AF45-65%"); line("AF_65_85","AF65-85%"); line("AF_gt85","AF>85%")
  print "--- 按 QUAL ---"
  line("Q_lt20","Q<20"); line("Q_20_50","Q20-50"); line("Q_50_100","Q50-100"); line("Q_gt100","Q>100")
  print "--- 按比对质量 MQ ---"
  line("MQ_lt50","MQ<50"); line("MQ_50_60","MQ50-60"); line("MQ_gt60","MQ>60")
  print "--- 交叉档（关键结论）---"
  line("CLEAN_het","干净杂合"); line("CLEAN_hom","干净纯合")
}
' "$TAB"

echo
echo "############### AF 直方图 ###############"
awk -F'\t' '{ ad=$9; n=split(ad,A,","); r=A[1]+0; v=A[2]+0; s=r+v
  if(s<=0) next
  b=int(v/s*25); if(b>24)b=24; H[b]++; tot++ }
END{ for(i=0;i<25;i++){ printf "  %.2f-%.2f %9d %s\n", i/25,(i+1)/25,H[i]+0,
  substr("##############################################################",1,int((H[i]+0)/tot*140)) } }' "$TAB"

echo
echo "############### 基因型构成 ###############"
awk -F'\t' '{g=$8; if(g!=""&&g!="."){gsub(/\|/,"/",g); print g}}' "$TAB" | sort | uniq -c | sort -rn | head -8
echo
log "完成 -> $OUT"
