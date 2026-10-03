#!/usr/bin/env bash
# test_align.sh —— 干净环境下实测单样本比对耗时
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
S=${1:-SRR11528381}
T=${2:-8}
rm -f /home/hugo/data/tmp/* 2>/dev/null

echo "=== 开始 $(date +%H:%M:%S)  样本=$S  线程=$T ==="
START=$(date +%s)

THREADS=$T DATA=/home/hugo/data bash /mnt/c/SF_data/tools/align_mm2_one.sh "$S"

END=$(date +%s)
echo "=== 结束 $(date +%H:%M:%S)  耗时 $((END-START)) 秒 ==="
ls -la /home/hugo/data/03_align/ 2>/dev/null
echo "--- flagstat ---"
cat /home/hugo/data/03_align/${S}.flagstat 2>/dev/null | head -8
