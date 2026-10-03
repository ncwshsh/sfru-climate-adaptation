#!/usr/bin/env bash
# diag_lowmap.sh —— 诊断低比对率样本：未比对 reads 的长度分布 + 序列样例 + 碱基组成
# 用法（WSL 内）: bash /mnt/c/SF_data/tools/diag_lowmap.sh
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
B=/mnt/c/SF_data/03_align

for S in SRR9289275 SRR9289270 SRR12044622 SRR9289272; do
  [ -s "$B/$S.dedup.bam" ] || continue
  echo "===== $S ====="
  echo "  -- flagstat 关键行 --"
  grep -E 'in total|primary mapped \(|primary duplicates|singletons' "$B/$S.flagstat" | sed 's/^/  /'
  echo "  -- 未比对 reads 抽样（0.2%）长度分布 --"
  samtools view -f4 -s 0.002 "$B/$S.dedup.bam" 2>/dev/null | awk '{print length($10)}' \
    | sort -n | awk '{a[NR]=$1} END{printf "  n=%d  min=%d  med=%d  max=%d\n", NR, a[1], a[int(NR/2)], a[NR]}'
  echo "  -- 已比对 reads 抽样（0.2%）长度分布 --"
  samtools view -F4 -s 0.002 "$B/$S.dedup.bam" 2>/dev/null | awk '{print length($10)}' \
    | sort -n | awk '{a[NR]=$1} END{printf "  n=%d  min=%d  med=%d  max=%d\n", NR, a[1], a[int(NR/2)], a[NR]}'
  echo "  -- 未比对 reads 前 3 条序列 --"
  samtools view -f4 "$B/$S.dedup.bam" 2>/dev/null | head -3 | awk '{print "  "substr($10,1,70)}'
  echo "  -- 已比对 reads 前 3 条序列 --"
  samtools view -F4 "$B/$S.dedup.bam" 2>/dev/null | head -3 | awk '{print "  "substr($10,1,70)}'
  echo
done
