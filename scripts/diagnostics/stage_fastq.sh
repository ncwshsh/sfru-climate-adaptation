#!/usr/bin/env bash
# stage_fastq.sh —— 把可用样本的 FASTQ 从 /mnt/c 搬到 WSL 原生盘
# 读 /mnt/c 的 dd 实测仅 3.2 MB/s，而 cp 到原生盘可达 123 MB/s（约 40 倍）
set -uo pipefail
LIST=/mnt/c/SF_data/tools/ready_samples.txt
TOOLS=/mnt/c/SF_data/tools
P=${1:-4}

mkdir -p /home/hugo/data/01_raw
echo "[$(date +%H:%M:%S)] 生成待搬列表"

grep -v '^#' "$LIST" | grep -v '^$' | tr -d '\r' | while read -r s; do
  echo "${s}_1"
  echo "${s}_2"
done > /tmp/stage_list.txt

total=$(wc -l < /tmp/stage_list.txt)
echo "待搬运文件数: $total"

xargs -P "$P" -I{} bash "${TOOLS}/copy_one.sh" {} < /tmp/stage_list.txt

echo "[$(date +%H:%M:%S)] 搬运结束"
n=$(ls /home/hugo/data/01_raw/*.fastq.gz 2>/dev/null | wc -l)
echo "原生盘已就位: ${n} 个文件 (预期 ${total})"
du -sh /home/hugo/data/01_raw
