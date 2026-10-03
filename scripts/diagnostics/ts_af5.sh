#!/usr/bin/env bash
# ts_af5.sh —— 对现有 5 样本 gate.vcf.gz 追加 AF（等位分数）轴重分析
# 目的：在不下载任何新数据的前提下，验证「AF 分层能否剥离测序误差」这一方法
# 关键量：site-level maxAF（携带 alt 的样本中最大的 alt 读数占比）
#   · 真变异：每个携带者 AF 都在 30-70%（杂合）或 >85%（纯合）
#   · 测序误差：通常只有 1 个携带者，且 AF 很低（几个 %）
# 若 Ts/Tv 随 maxAF 升到 0.5 附近而落到 ~1.3 平台 -> 该物种真实值就是 ~1.3
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
VAR=/home/hugo/data/04_variant
V=$VAR/gate.vcf.gz
[ -s "$V" ] || { echo "缺 $V"; exit 1; }
echo "[$(date '+%H:%M:%S')] 流式重分析 $V（不落盘中间文件）"

bcftools query -f '%REF\t%ALT\t%QUAL\t%INFO/DP[\t%GT\t%AD]\n' "$V" 2>/dev/null | awk -F'\t' '
function ists(r,a){ return ((r=="A"&&a=="G")||(r=="G"&&a=="A")||(r=="C"&&a=="T")||(r=="T"&&a=="C")) }
function reg(k,ist){ N[k]++; if(ist) TS[k]++; else TV[k]++ }
{
  ref=$1; alt=$2; q=$3+0; dp=$4+0
  if(length(ref)!=1 || length(alt)!=1) next
  if(ref==alt || alt=="." || alt=="<*>") next
  ac=0; car=0; maxaf=0; naf=0
  for(i=5;i<=NF;i+=2){
    g=$(i); ad=$(i+1)
    gsub(/\|/,"/",g)
    m=split(ad,A,","); r=A[1]+0; v=A[2]+0; s=r+v
    af=0; if(s>0) af=v/s
    has=0
    if(g ~ /\//){ k=split(g,B,"/"); for(j=1;j<=k;j++){ if(B[j]!="." && B[j]!="0"){ ac++; has=1 } } }
    else { if(g!="0" && g!="."){ ac++; has=1 } }
    if(has){ car++; if(af>maxaf) maxaf=af; naf++ }
  }
  if(ac==0) next
  ist=ists(ref,alt)
  reg("ALL",ist)
  if(car==1)reg("CAR1",ist); else if(car==2)reg("CAR2",ist); else if(car<=4)reg("CAR3_4",ist); else reg("CAR5p",ist)
  if(maxaf<0.1)reg("MAF_lt10",ist); else if(maxaf<0.2)reg("MAF_10_20",ist); else if(maxaf<0.3)reg("MAF_20_30",ist); else if(maxaf<0.4)reg("MAF_30_40",ist); else if(maxaf<0.6)reg("MAF_40_60",ist); else reg("MAF_60p",ist)
  if(dp<10)reg("DP_lt10",ist); else if(dp<20)reg("DP_10_20",ist); else if(dp<45)reg("DP_20_45",ist); else if(dp<90)reg("DP_45_90",ist); else reg("DP_gt90",ist)
  if(q>=50 && car>=2 && maxaf>=0.35) reg("CONF",ist)
  if(car==1 && maxaf<0.15) reg("ERR",ist)
  tot++
}
function line(k,label, n1,v1){ n1=N[k]+0; v1=TV[k]+0
  printf "  %-14s n=%-9d Ts=%-8d Tv=%-8d Ts/Tv=%s\n", label, n1, TS[k]+0, v1, (v1>0? sprintf("%.3f",(TS[k]+0)/v1):"NA") }
END{
  printf "  总位点(有alt)=%d\n\n", tot
  print "--- 总体 ---"; line("ALL","ALL")
  print "--- 按携带样本数 carriers ---"
  line("CAR1","car1"); line("CAR2","car2"); line("CAR3_4","car3-4"); line("CAR5p","car>=5")
  print "--- 按 site maxAF（关键新轴）---"
  line("MAF_lt10","maxAF<10%"); line("MAF_10_20","10-20%"); line("MAF_20_30","20-30%"); line("MAF_30_40","30-40%"); line("MAF_40_60","40-60%"); line("MAF_60p","maxAF>=60%")
  print "--- 按位点深度 ---"
  line("DP_lt10","DP<10"); line("DP_10_20","DP10-20"); line("DP_20_45","DP20-45"); line("DP_45_90","DP45-90"); line("DP_gt90","DP>90")
  print "--- 交叉判据 ---"
  line("CONF","Q>=50 & car>=2 & mAF>=35%")
  line("ERR","car=1 & mAF<15%（疑误差）")
}
'
echo "[$(date '+%H:%M:%S')] 完成"
