#!/usr/bin/env bash
# run_align_s2.sh —— S2 队列批量比对调度器（WSL 内运行）
#
# 从 cohort_formal_s2.tsv 读 220 样本，2 并发 × 每样本 8 线程 bwa mem。
# CN 10 个样本自动识别为 interleaved（module=CN）。
# 幂等：已有 dedup.bam+bai 的样本跳过（align_s2_one.sh 内部判）。
#
# 用法:
#   wsl -d Ubuntu-24.04 -e bash /mnt/c/SF_data/tools/run_align_s2.sh < /dev/null
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

TOOLS=/mnt/c/SF_data/tools
TSV=$TOOLS/cohort_formal_s2.tsv
ALN=/mnt/c/SF_data/03_align
CONC=${CONC:-2}          # 并发样本数
THREADS=${THREADS:-8}    # 每样本 bwa 线程
TAG=${TAG:-k15}          # 输出标签（k15/k19），便于并存对照
MINSEED=${MINSEED:-15}  # bwa -k
LOG=$TOOLS/align_s2_chain.log

mkdir -p "$ALN"

echo "[$(date '+%F %T')] ======== S2 批量比对开始 并发=$CONC 线程=$THREADS ========" | tee -a "$LOG"

# 构造任务清单：SRR \t interleaved(0/1)
awk -F'\t' 'NR>1{print $1"\t"($3=="CN"?1:0)}' "$TSV" > /tmp/.align_jobs.$$.tsv
n=$(wc -l < /tmp/.align_jobs.$$.tsv)
echo "[$(date '+%T')] 队列 $n 个样本" | tee -a "$LOG"

export TOOLS ALN THREADS TAG MINSEED LOG

run_one() {
  local s="$1" inter="$2"
  bash "$TOOLS/align_s2_one.sh" "$s" $([ "$inter" = "1" ] && echo --interleaved) \
    > "${ALN}/${s}.align.out" 2>&1
  local rc=$?
  local tag="ok"
  [ "$rc" -ne 0 ] && tag="FAIL rc=$rc"
  grep -q "SKIP" "${ALN}/${s}.align.out" 2>/dev/null && tag="skip"
  echo "[$(date '+%T')] $s  $tag" >> "$LOG"
  return 0
}
export -f run_one

# xargs 并发调度
< /tmp/.align_jobs.$$.tsv xargs -d '\n' -n 1 -P "$CONC" -I {} bash -c '
  s=$(echo "{}" | cut -f1); inter=$(echo "{}" | cut -f2)
  run_one "$s" "$inter"
'
rm -f /tmp/.align_jobs.$$.tsv

echo "[$(date '+%F %T')] ======== S2 批量比对结束 ========" | tee -a "$LOG"
echo "  成功 BAM: $(ls "$ALN"/*.dedup.bam 2>/dev/null | grep -c . || echo 0)" | tee -a "$LOG"
