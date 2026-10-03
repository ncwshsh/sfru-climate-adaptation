#!/usr/bin/env bash
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
echo "=== 工具检查 ==="
for t in pigz zstd bwa samtools minimap2 bgzip; do
  printf "%-10s %s\n" "$t" "$(command -v "$t" 2>/dev/null || echo MISSING)"
done
echo
echo "=== 当前比对进度 ==="
ls -la --time-style=+%H:%M /home/hugo/data/tmp/ 2>/dev/null
echo "--- 进程 ---"
ps -eo pcpu,etime,comm --sort=-pcpu | head -4
date "+现在 %H:%M:%S"
