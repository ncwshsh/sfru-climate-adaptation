#!/usr/bin/env bash
# probe_pure.sh —— 在已缓存的 tab 上探查「极限纯净子集」的 Ts/Tv 上限
# 用法: bash probe_pure.sh /home/hugo/data/tmp/<prefix>.tab
set -uo pipefail
TAB="${1:?需要 tab 文件}"
awk -F'\t' '
function ists(r,a){ return ((r=="A"&&a=="G")||(r=="G"&&a=="A")||(r=="C"&&a=="T")||(r=="T"&&a=="C")) }
function L(k,label, n1,v1){ n1=N[k]+0; v1=V[k]+0
  printf "  %-34s n=%-9d Ts/Tv=%s\n", label, n1, (v1>0? sprintf("%.3f",S[k]/v1):"NA") }
{
  ref=$3; alt=$4; q=$5+0; mq=$7+0; ad=$9; dp=$10+0
  if(length(ref)!=1 || length(alt)!=1 || ref==alt || alt=="." || alt=="<*>") next
  n=split(ad,A,","); r=A[1]+0; v=A[2]+0; s=r+v
  if(s<=0) next
  af=v/s; ist=ists(ref,alt)
  key=""
  if(q>=100 && mq>=60 && dp>=20 && dp<45 && af>=0.40 && af<=0.60) key="A"
  else if(q>=100 && mq>=60 && dp>=20 && dp<45 && af>=0.90)       key="B"
  else if(q>=50  && mq>=50 && dp>=20 && dp<45)                   key="C"
  else if(q>=100 && mq>=60 && dp>=45 && dp<90)                   key="D"
  else if(q>=50  && mq>=50 && dp>=10)                            key="E"
  if(key!=""){ N[key]++; if(ist) S[key]++; else V[key]++ }
}
END{
  L("A","A 全轴拉满·平衡杂合(最纯)")
  L("B","B 全轴拉满·纯合")
  L("C","C 中档  DP20-45 全收")
  L("D","D 高端  DP45-90 全收")
  L("E","E 宽口  DP>=10 全收")
}
' "$TAB"
