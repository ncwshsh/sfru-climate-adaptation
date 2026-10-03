#!/usr/bin/env bash
# dpstat.sh —— 从 ts_deep2 的 tab 里取 mpileup 实际深度统计（第 6 列 = INFO/DP）
set -uo pipefail
for f in "$@"; do
  [ -s "$f" ] || { echo "$f 不存在"; continue; }
  printf '%-22s ' "$(basename "$f" .tab)"
  cut -f6 "$f" | sort -n | awk '{a[NR]=$1; s+=$1} END{printf "DP中位=%-5d DP均值=%-6.1f 位点=%d\n", a[int(NR/2)+1], s/NR, NR}'
done
