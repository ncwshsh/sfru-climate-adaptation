#!/usr/bin/env bash
# ts_deep.sh —— 单深样本（>=20x）一击定性真实 Ts/Tv 上限
#
# 相比 ts_gate.sh（5 浅样本联合）的升级：
#   1. 单样本无法用 carriers，改用 DP 轴 + 新增 AF（alt 读数占比）轴
#      · 测序误差：DP=30 里混进 1 个错读 -> AF≈3%
#      · 真杂合  ：AF≈50%
#      => 按 AF 分层可把误差直接剥离，无需额外数据
#   2. 报 het/hom 比（>~2x 基线 => 塌缩重复，该档 Ts/Tv 不可信）
#   3. 报 MQ 轴，排除错配区
# 判据:
#   AF 高 & DP 高 & MQ 高的档位若 Ts/Tv 稳定在 ~1.30  -> 闸门 1.8 设错，应下调
#   若该档 Ts/Tv 继续爬升接近 1.6+          -> 数据量仍不足，需更深
#
# 用法: bash ts_deep.sh <BAM> <前缀> [染色体数=8] [线程=16]
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
DATA=/home/hugo/data
REF=$DATA/ref/ref_GCF_023101765.2.fna
VAR=$DATA/04_variant
TMP=$DATA/tmp
BAM="${1:?需要 BAM 路径}"
PREFIX="${2:?需要前缀}"
NCHR="${3:-8}"
THREADS="${4:-16}"
OUT=$VAR/${PREFIX}.vcf.gz
LOG=$VAR/${PREFIX}.log
mkdir -p "$VAR" "$TMP"
log(){ printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "$LOG"; }

REG=$(sort -k2,2 -rn "${REF}.fai" | head -"$NCHR" | cut -f1 | paste -sd, -)
GLEN=$(sort -k2,2 -rn "${REF}.fai" | head -"$NCHR" | awk '{s+=$2} END{print s}')
log "样本=$BAM"
log "区域: $NCHR 条最大染色体, 共 $((GLEN/1000000)) Mb  线程=$THREADS"

if [ ! -s "$OUT" ]; then
  log "mpileup+call 开始（单样本，改用 -d 1000 避免高深度被降采样）"
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
if [ "$NREC" -eq 0 ]; then log "[FATAL] 无记录"; exit 1; fi

TAB=$TMP/${PREFIX}.tab
bcftools query -f '%CHROM\t%POS\t%REF\t%ALT\t%QUAL\t%INFO/DP\t%INFO/MQ\t[%GT\t%AD\t%DP]\n' "$OUT" > "$TAB"
log "导出 $TAB ($(wc -l < "$TAB") 行)"

echo
echo "===================== Ts/Tv 分层（单样本 $PREFIX）====================="
awk -F'\t' '
function ists(r,a){ return ((r=="A"&&a=="G")||(r=="G"&&a=="A")||(r=="C"&&a=="T")||(r=="T"&&a=="C")) }
function reg(k,ist){ N[k]++; if(ist) TS[k]++; else TV[k]++ }
{
  ref=$3; alt=$4; q=$5+0; mq=$7+0; gt=$8; ad=$9; dp=$10+0
  if(length(ref)!=1 || length(alt)!=1) next
  if(ref==alt || alt=="." || alt=="<*>") next
  n=split(ad,A,","); r=A[1]+0; v=A[2]+0; s=r+v
  if(s<=0) next
  af=v/s
  ist=ists(ref,alt)
  reg("ALL",ist)
  if(dp<5)reg("DP_lt5",ist); else if(dp<10)reg("DP_5_10",ist); else if(dp<20)reg("DP_10_20",ist); else if(dp<30)reg("DP_20_30",ist); else if(dp<45)reg("DP_30_45",ist); else if(dp<60)reg("DP_45_60",ist); else if(dp<90)reg("DP_60_90",ist); else reg("DP_gt90",ist)
  if(af<0.1)reg("AF_lt10",ist); else if(af<0.2)reg("AF_10_20",ist); else if(af<0.3)reg("AF_20_30",ist); else if(af<0.4)reg("AF_30_40",ist); else if(af<0.6)reg("AF_40_60",ist); else if(af<0.8)reg("AF_60_80",ist); else reg("AF_gt80",ist)
  if(q<20)reg("Q_lt20",ist); else if(q<50)reg("Q_20_50",ist); else if(q<100)reg("Q_50_100",ist); else reg("Q_gt100",ist)
  if(mq<40)reg("MQ_lt40",ist); else if(mq<50)reg("MQ_40_50",ist); else if(mq<60)reg("MQ_50_60",ist); else reg("MQ_gt60",ist)
  g=gt; gsub(/\|/,"/",g)
  if(g=="0/1")reg("GT_het",ist); else if(g=="1/1")reg("GT_hom",ist); else reg("GT_other",ist)
  # 交叉档：误差被剥干净的"真变异"近似集
  if(q>=50 && mq>=50 && dp>=20 && af>=0.35 && af<=0.65) reg("CLEAN_het",ist)
  if(q>=50 && mq>=50 && dp>=20 && af>=0.85) reg("CLEAN_hom",ist)
  if(q>=50 && mq>=50 && dp>=20 && af<0.15) reg("DIRTY_lowaf",ist)
  tot++
}
function line(k,label,  n1,v1){
  n1=N[k]+0; v1=TV[k]+0
  printf "  %-16s n=%-9d Ts=%-8d Tv=%-8d Ts/Tv=%s\n", label, n1, TS[k]+0, v1, (v1>0? sprintf("%.3f",(TS[k]+0)/v1):"NA")
}
END{
  printf "  总位点(有alt)=%d\n\n", tot
  print "--- 总体 ---";                 line("ALL","ALL")
  print "--- 按深度 DP ---"
  line("DP_lt5","DP<5"); line("DP_5_10","DP5-10"); line("DP_10_20","DP10-20"); line("DP_20_30","DP20-30"); line("DP_30_45","DP30-45"); line("DP_45_60","DP45-60"); line("DP_60_90","DP60-90"); line("DP_gt90","DP>90")
  print "--- 按等位分数 AF = alt/(ref+alt) ---"
  line("AF_lt10","AF<10%"); line("AF_10_20","AF10-20%"); line("AF_20_30","AF20-30%"); line("AF_30_40","AF30-40%"); line("AF_40_60","AF40-60%"); line("AF_60_80","AF60-80%"); line("AF_gt80","AF>80%")
  print "--- 按 QUAL ---"
  line("Q_lt20","Q<20"); line("Q_20_50","Q20-50"); line("Q_50_100","Q50-100"); line("Q_gt100","Q>100")
  print "--- 按比对质量 MQ ---"
  line("MQ_lt40","MQ<40"); line("MQ_40_50","MQ40-50"); line("MQ_50_60","MQ50-60"); line("MQ_gt60","MQ>60")
  print "--- 按基因型 ---"
  line("GT_het","het"); line("GT_hom","hom"); line("GT_other","other")
  print "--- 交叉档（关键结论）---"
  line("CLEAN_het","干净杂合"); line("CLEAN_hom","干净纯合"); line("DIRTY_lowaf","低AF(疑误差)")
  printf "\n  het/hom 比 = %.3f  (基线约 0.35，>0.7 提示塌缩重复)\n", (N["GT_hom"]>0? (N["GT_het"]+0)/(N["GT_hom"]+0) : 0)
}
' "$TAB"

echo
echo "===================== AD 分布与 AF 直方图 ====================="
awk -F'\t' '
{ ad=$9; n=split(ad,A,","); r=A[1]+0; v=A[2]+0; s=r+v
  if(s<=0) next
  af=v/s
  b=int(af*20); if(b>19) b=19
  H[b]++; tot++
}
END{
  for(i=0;i<20;i++){
    lbl=sprintf("%.2f-%.2f", i/20, (i+1)/20)
    printf "  %s  %8d  %s\n", lbl, H[i]+0, substr("############################################################", 1, int((H[i]+0)/tot*150))
  }
}' "$TAB"

echo
echo "===================== 基因型构成 ====================="
awk -F'\t' '{g=$8; if(g!=""&&g!="."){gsub(/\|/,"/",g); print g}}' "$TAB" | sort | uniq -c | sort -rn | head -8
echo
log "完成 -> $OUT"
