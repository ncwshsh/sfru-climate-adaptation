#!/bin/bash
export PATH=/home/hugo/mamba/envs/sfru/bin:/usr/bin:/bin
echo "===== WSL 01_raw 文件命名形态 ====="
ls /home/hugo/data/01_raw/ | sed 's/^SRR[0-9]*_//' | sort | uniq -c | sort -rn | head -10
echo
echo "===== 已落盘样本（双端齐全）====="
ls /home/hugo/data/01_raw/ | grep -oE '^(SRR|ERR)[0-9]+' | sort -u > /tmp/have_runs.txt
wc -l < /tmp/have_runs.txt
echo
echo "===== 现有 dedup.bam 的真实深度（idxstats 估算法）====="
GEN=383923118
printf "%-14s %14s %10s\n" "run" "mapped_reads" "depth_x"
for f in /home/hugo/data/03_align/*.dedup.bam; do
  [ -f "$f" ] || continue
  s=$(basename "$f" .dedup.bam)
  m=$(samtools idxstats "$f" 2>/dev/null | awk -F'\t' '{s+=$3} END{print s+0}')
  awk -v s="$s" -v m="$m" -v g="$GEN" 'BEGIN{printf "%-14s %14d %10.2f\n", s, m, m*150/g}'
done
echo
echo "===== 参考基因组长度核对 ====="
awk '{s+=$2} END{print "fai 总长 =", s}' /home/hugo/data/ref/ref_GCF_023101765.2.fna.fai
