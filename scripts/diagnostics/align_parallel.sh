#!/usr/bin/env bash
# align_parallel.sh —— 并行为一批样本做「比对 -> 去重 -> 索引」
# 用法: bash align_parallel.sh <样本列表(每行一个SRR)> [并行路数] [每路线程数]
set -u
export PATH="/usr/bin:/bin:$PATH"

LIST="${1:?需要样本列表}"
P="${2:-5}"
T="${3:-4}"

HERE=/mnt/c/SF_data/tools
mkdir -p /mnt/c/SF_data/tmp

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }
log "并行比对启动: 并行 ${P} 路 x 每路 ${T} 线程"

grep -v '^#' "$LIST" | grep -v '^$' \
  | THREADS="$T" xargs -P "$P" -I{} bash -c "bash ${HERE}/align_one.sh {} || echo '[{}] ERROR'" \
  2>&1 | tee /mnt/c/SF_data/03_align/align_$(date +%m%d_%H%M).log

log "比对批次结束"
