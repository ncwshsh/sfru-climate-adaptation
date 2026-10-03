#!/usr/bin/env bash
# diag_bam.sh —— 从 BAM 直接诊断比对质量（NM 错配 / MAPQ / 碱基质量 / 插入片段）
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
B=${1:-/home/hugo/data/03_align/SRR10980085.dedup.bam}
N=${2:-200000}

echo "===== 诊断 $B （采样 $N 条）====="
samtools view -F 0x904 -q 0 "$B" NC_064212.1:1-8000000 2>/dev/null | head -"$N" | awk '
{
  nm=-1
  for(i=12;i<=NF;i++){ if($i ~ /^NM:i:/) nm=substr($i,6)+0 }
  mq=$5+0
  len=length($10)
  q=$11
  bq=0
  for(j=1;j<=length(q);j++) bq += index("!\"#$%&\x27()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~", substr(q,j,1)) - 1
  if(length(q)>0) bq = bq/length(q)
  tl=$9+0; if(tl<0) tl=-tl

  n++; s_nm+=nm; s_mq+=mq; s_bq+=bq; s_len+=len; s_tl+=tl
  if(nm==0) nm0++
  if(nm>=1) nm1p++
  if(nm>4) hi_nm++
  if(mq<20) lo_mq++
  if(tl>1000) big_tl++
}
END{
  printf "reads            = %d\n", n
  printf "平均 read 长度    = %.0f bp\n", s_len/n
  printf "平均碱基质量      = Q%.1f\n", s_bq/n
  printf "平均 MAPQ        = %.1f\n", s_mq/n
  printf "MAPQ<20 占比     = %.1f%%\n", 100*lo_mq/n
  printf "平均 NM(错配数)   = %.2f\n", s_nm/n
  printf "NM==0 占比       = %.1f%%   <- 完全匹配\n", 100*nm0/n
  printf "NM>=1 占比       = %.1f%%\n", 100*nm1p/n
  printf "NM>4  占比       = %.1f%%   <- 严重错配\n", 100*hi_nm/n
  printf "平均插入片段      = %.0f bp\n", s_tl/n
  printf "插入片段>1000 占比 = %.1f%%\n", 100*big_tl/n
}'

echo
echo "===== 前 3 条 read 原文（看 flag / MAPQ / CIGAR / NM）====="
samtools view -F 0x904 -q 0 "$B" NC_064212.1:1-8000000 2>/dev/null | head -3

echo
echo "===== 抽样 200 条 read 的 markdup/BQ 原始质量行 ====="
samtools view -F 0x904 -q 0 "$B" NC_064212.1:1-8000000 2>/dev/null | head -200 \
  | awk '{q=$11; s=0; for(j=1;j<=length(q);j++) s += index("!\"#$%&\x27()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~", substr(q,j,1)) - 1; printf "%s ", (length(q)>0? s/length(q):0)} END{print ""}' \
  | tr ' ' '\n' | grep -v '^$' | sort -g | awk '{a[NR]=$1} END{printf "  单条 read 平均 BQ: 最低=%.1f  p25=%.1f  中位=%.1f  p75=%.1f  最高=%.1f\n", a[1], a[int(NR*0.25)], a[int(NR*0.5)], a[int(NR*0.75)], a[NR]}'
