#!/usr/bin/env bash
# align_parallel_mm2.sh —— 并行比对（minimap2 版）
# 用法: bash align_parallel_mm2.sh <样本列表> [并行路数] [每路线程数]
# 数据默认走 WSL 原生盘 /home/hugo/data（读 /mnt/c 实测仅 3.2 MB/s，原生盘可达 123 MB/s）
set -uo pipefail
export PATH="/usr/bin:/bin:$PATH"
LIST="${1:?需要样本列表}"
P="${2:-5}"
T="${3:-4}"
DATA=${DATA:-/home/hugo/data}
HERE=/mnt/c/SF_data/tools

mkdir -p "${DATA}/tmp" "${DATA}/03_align"

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }
log "minimap2 并行比对: ${P} 路 x ${T} 线程  (数据根 ${DATA})"

# ⚠️ tr -d '\r' 必须保留：Windows 侧生成的列表是 CRLF，WSL 下文件名会平白多出 \r
grep -v '^#' "$LIST" | grep -v '^$' | tr -d '\r' \
  | xargs -P "$P" -I{} bash -c "DATA=$DATA THREADS=$T bash ${HERE}/align_mm2_one.sh {} || echo '[{}] ERROR'" \
  2>&1 | tee "${DATA}/03_align/align_mm2_$(date +%m%d_%H%M).log"

log "批次结束，已产出 dedup.bam: $(ls ${DATA}/03_align/*.dedup.bam 2>/dev/null | wc -l) 个"
