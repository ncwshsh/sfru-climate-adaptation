#!/usr/bin/env bash
# check_pair_sync.sh —— 验证 R1/R2 是否「按行序配对」同步（低比对率的疑似根因）
# 原理：bwa mem 假定 R1 第 i 条与 R2 第 i 条是同一对。
#   若两文件按字节比例采样后保留的记录数不同（N1 != N2），前 min(N1,N2) 条之后整体错位
#   → 大量"假配对"，比对率暴跌（实测最低 21%）。
# 判据：抽取第 1 / 100000 / 500000 / 末条 read 名，R1 与 R2 的 read 编号必须一致。
# 用法（WSL 内）: bash /mnt/c/SF_data/tools/check_pair_sync.sh <SRR> <R1> <R2>
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
S="$1"; R1="$2"; R2="$3"

n1=$(gzip -dc "$R1" 2>/dev/null | wc -l | awk '{print $1/4}')
n2=$(gzip -dc "$R2" 2>/dev/null | wc -l | awk '{print $1/4}')
echo "== $S =="
echo "  记录数: R1=$n1  R2=$n2  差 $(awk -v a=$n1 -v b=$n2 'BEGIN{printf "%.1f%%", (b-a)*100/a}')"

for k in 1 100000 500000; do
  h1=$(gzip -dc "$R1" 2>/dev/null | awk -v k=$k 'NR%4==1 && ++c==k {print $1; exit}')
  h2=$(gzip -dc "$R2" 2>/dev/null | awk -v k=$k 'NR%4==1 && ++c==k {print $1; exit}')
  # 去掉 /1 /2 后缀后比较
  a=${h1%/*}; b=${h2%/*}
  if [ "$a" = "$b" ]; then s="✅同步"; else s="❌错位"; fi
  echo "  第 $k 条: R1=$h1  R2=$h2  $s"
done
