#!/usr/bin/env bash
# 批量修复被截断的 gzip
set -u
cd /c/SF_data/01_raw || exit 1
ls | grep -E '\.partial[0-9]+$' | sed 's|^|/c/SF_data/01_raw/|' > /c/SF_data/tools/repair_list.txt
echo "待修复: $(wc -l < /c/SF_data/tools/repair_list.txt)"
xargs -P 8 -I{} bash /c/SF_data/tools/repair_one.sh {} < /c/SF_data/tools/repair_list.txt
echo "=== 修复阶段结束 ==="
echo "成品数: $(ls /c/SF_data/01_raw/*.fastq.gz 2>/dev/null | wc -l)"
