#!/usr/bin/env bash
# restart_align.sh —— 安全重起 S2 比对链（在 WSL 内运行）
#
# 为什么需要它：
#   2026-09-20 事故——上层调度被打死后，在跑的样本变孤儿；新链从队首重新扫，
#   对同一批样本又开了一份，两条管线同时写同一个 OUTBAM（还共用同一份 TMP）。
#   现在 align_s2_one.sh 里有 /tmp 原子目录锁（记 PID），所以**重起前不必等排空**：
#   新链遇到正在跑的样本会打 BUSY 并跳过，它们在跑的那份会自己写完。
#
# 用法:
#   bash /mnt/c/SF_data/tools/restart_align.sh [CONC] [THREADS] [TAG] [MINSEED] [ALIGNER] [SAMT] [SMEM] [KILLALL]
#   例: bash restart_align.sh 2 9 bm2k15 15 bm2 2 1G 0
#
# ★ 内存预算（2026-09-20 实测，23 GB 机器）：
#     bwa-mem2 RSS ≈ 1.5 GB(共享索引) + 0.61 GB × 线程数
#       -t6 → 5.2 GB/个；-t10 → 7.6 GB/个
#     后处理排序峰值 ≈ SAMT × SMEM
#       SAMT=3/SMEM=1500M → 4.5 GB/个，两个同时 = 9 GB → **总计 23 GB，撑爆**
#       SAMT=2/SMEM=1G    → 2 GB/个，两个同时 = 4 GB → 总计约 18 GB，留 5 GB 余量 ✅
#   ⇒ 别再往上加 SAMT/SMEM，比对线程也别超过 9
#
# ⚠️ 不要在 WSL 里用 nohup ... &（实测会被杀）。本脚本最后 exec 成前台链，
#    生命周期交给调用方（Bash 工具 run_in_background）托管。
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

CONC=${1:-2}
THREADS=${2:-8}
TAG=${3:-bm2k15}
MINSEED=${4:-15}
ALIGNER=${5:-bm2}
SAMT=${6:-2}
SMEM=${7:-1G}
KILLALL=${8:-0}        # =1 连在跑的工作进程一起杀（内存告急 / 要立刻换参数时用）
TOOLS=/mnt/c/SF_data/tools
ALN=/mnt/c/SF_data/03_align
LOG=$TOOLS/align_s2_chain.log

echo "===== $(date '+%F %T') 重起 S2 比对链  CONC=$CONC THREADS=$THREADS TAG=$TAG -k=$MINSEED ALIGNER=$ALIGNER SAMT=$SAMT SMEM=$SMEM ====="

# ---------- 1. 杀调度，默认不动在跑的工作进程 ----------
echo "--- 杀调度 ---"
pkill -f 'run_align_s2.sh' 2>/dev/null && echo "  已杀 run_align_s2.sh" || echo "  无 run_align_s2.sh"
pkill -f 'xargs -d'        2>/dev/null && echo "  已杀 xargs 调度"       || echo "  无 xargs"
sleep 2

if [ "$KILLALL" = "1" ]; then
  echo "--- KILLALL：连工作进程一起杀 ---"
  pkill -f 'align_s2_one.sh' 2>/dev/null && echo "  已杀 align_s2_one.sh"
  pkill -x 'bwa-mem2.avx2'   2>/dev/null && echo "  已杀 bwa-mem2"
  pkill -x 'bwa'             2>/dev/null && echo "  已杀 bwa"
  pkill -x 'samtools'        2>/dev/null && echo "  已杀 samtools"
  sleep 3
  # 清掉「写到一半」的产物：有 BAM 但没 .bai 的一律视为未完成，删掉让它重跑
  n=0
  for b in "$ALN"/*.dedup.bam; do
    [ -f "$b" ] || continue
    if [ ! -s "${b}.bai" ]; then echo "  删半成品 $(basename "$b")"; rm -f "$b"; n=$((n+1)); fi
  done
  echo "  清半成品: $n 个"
fi

# ---------- 2. 可选排空 ----------
if [ "${DRAIN:-0}" = "1" ]; then
  echo "--- 等待在跑样本排空 ---"
  while pgrep -x bwa >/dev/null 2>&1 || pgrep -x samtools >/dev/null 2>&1; do
    echo "  $(date '+%T') 仍在跑: $(pgrep -x bwa | wc -l) bwa / $(pgrep -x samtools | wc -l) samtools"
    sleep 60
  done
else
  echo "--- 不排空：靠 /tmp 互斥锁防止重复跑（当前在跑 $(ps -ef | grep -c '[a]lign_s2_one.sh') 个）---"
fi

# ---------- 3. 清陈旧锁（PID 已死的） ----------
n=0
for d in /tmp/.aln_lock_*; do
  [ -d "$d" ] || continue
  pid=$(cat "$d/pid" 2>/dev/null)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then :; else rm -rf "$d"; n=$((n+1)); fi
done
echo "  清理陈旧锁: $n 个"

# ---------- 4. 起新链 ----------
echo "--- 起新链 ---"
export CONC THREADS TAG MINSEED ALIGNER SAMT SMEM
echo "[$(date '+%F %T')] ======== 重起：并发=$CONC 线程=$THREADS TAG=$TAG -k=$MINSEED 比对器=$ALIGNER SAMT=$SAMT SMEM=$SMEM ========" | tee -a "$LOG"
exec bash "$TOOLS/run_align_s2.sh"
