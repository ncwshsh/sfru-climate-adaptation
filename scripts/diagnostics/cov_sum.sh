#!/usr/bin/env bash
# cov_sum.sh —— 汇总 samtools coverage 表
set -uo pipefail
F="${1:?需要覆盖表}"
[ -s "$F" ] || { echo "文件不存在或为空: $F"; exit 1; }
echo "行数=$(wc -l < "$F")"
head -1 "$F"
awk 'NR>1 && $3>1000000 {n++; num+=$7*$3; den+=$3; cov+=$5; tot+=$3; if($7<8)low++; if($7<12)low12++}
     END{printf "染色体数=%d\n可用加权均值深度=%.2f x\n被覆盖(>=1x)碱基=%.1f%%\n均值<8x的染色体=%d\n均值<12x的染色体=%d\n", n, num/den, 100*cov/tot, low+0, low12+0}' "$F"
echo "--- 可用深度最低 3 条 ---"
awk 'NR>1 && $3>1000000' "$F" | sort -k7,7n | head -3
echo "--- 可用深度最高 3 条 ---"
awk 'NR>1 && $3>1000000' "$F" | sort -k7,7nr | head -3
echo "--- 全库(scaffold 一并)最高 8 条（含坍缩重复）---"
awk 'NR>1' "$F" | sort -k7,7nr | head -8
echo "--- 被覆盖碱基占比最低 3 条 ---"
awk 'NR>1 && $3>1000000' "$F" | sort -k5,5n | head -3
