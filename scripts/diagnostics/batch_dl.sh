#!/usr/bin/env bash
# batch_dl.sh —— 按清单批量下载 ENA FASTQ（部分下载，统一降覆盖）
# 用法: bash batch_dl.sh <清单tsv> [起始行] [结束行] [并发] [块MB]
# 清单格式: run \t country \t region \t depth_x \t pct_to_download \t study
set -u
export PATH="/usr/bin:/bin:$PATH"

LIST="${1:?需要清单文件}"
FROM="${2:-1}"
TO="${3:-999999}"
W="${4:-8}"
BS="${5:-16}"
OUT="C:/SF_data/01_raw"
HERE="$(cd "$(dirname "$0")" && pwd)"

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

n=0; done_n=0; skip_n=0; fail_n=0
while IFS=$'\t' read -r run country region depth pct study; do
  n=$((n+1))
  [ "$n" -lt "$FROM" ] && continue
  [ "$n" -gt "$TO" ] && break
  case "$run" in run|''|'#'*) continue;; esac

  # 已完成判定：任一 partialN 或完整文件存在
  if ls "/c/SF_data/01_raw/${run}_1.fastq.gz"* >/dev/null 2>&1; then
    log "[$n] $run 已存在，跳过 ($country ${depth}x)"
    skip_n=$((skip_n+1)); continue
  fi

  log "[$n] $run | $country | ${depth}x -> 取前 ${pct}% | $study"
  if bash "${HERE}/dl_ena.sh" "$run" "$W" "$BS" "$OUT" "$pct" > "/c/SF_data/01_raw/.log_${run}.txt" 2>&1; then
    done_n=$((done_n+1))
  else
    fail_n=$((fail_n+1))
    log "[$n] $run 未完成（保留分块，重跑可续传）"
  fi
done < "$LIST"

log "批次结束: 完成 $done_n / 跳过 $skip_n / 未完成 $fail_n"
