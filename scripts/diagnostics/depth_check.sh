#!/bin/bash
export PATH=/home/hugo/mamba/envs/sfru/bin:/usr/bin:/bin
for S in SRR10980085 SRR11528381 SRR11528382 SRR12044628 SRR12044633; do
  B=/home/hugo/data/03_align/${S}.dedup.bam
  [ -f "$B" ] || { echo "$S 无 bam"; continue; }
  echo "=========== $S ==========="
  samtools flagstat "$B" | head -14
  echo "  --- 全基因组平均深度 ---"
  samtools depth -a "$B" 2>/dev/null | awk '{s+=$3; n++} END{printf "  平均深度=%.2f  (统计位点 %d / 基因组 %.1f Mb)\n", s/n, n, n/1e6}'
done
