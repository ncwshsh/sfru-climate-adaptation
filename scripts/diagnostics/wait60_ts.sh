#!/usr/bin/env bash
# wait60_ts.sh —— 等 60% 比对写出 "=== end ===" 后，自动对成品 BAM 跑 Ts/Tv 分层
# 用法: wsl -d Ubuntu-24.04 -- bash /mnt/c/SF_data/tools/wait60_ts.sh < /dev/null
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
ALN=/home/hugo/data/03_align
LOG=${ALN}/SRR12044649_60_run.log
BAM=${ALN}/SRR12044649_60.dedup.bam
WAITLOG=${ALN}/wait60_ts.log

echo "[$(date '+%F %T')] 等待 60% 比对完成 ..." | tee -a "$WAITLOG"
for i in $(seq 1 900); do          # 最多等 150 分钟
  if grep -q '^=== end ===$' "$LOG" 2>/dev/null; then
    echo "[$(date '+%F %T')] 比对已完成" | tee -a "$WAITLOG"; break
  fi
  sleep 10
done

if [ ! -s "$BAM" ]; then
  echo "[$(date '+%F %T')] [FATAL] 成品 BAM 不存在：$BAM" | tee -a "$WAITLOG"; exit 1
fi

echo "[$(date '+%F %T')] 开始 Ts/Tv 分层" | tee -a "$WAITLOG"
bash /mnt/c/SF_data/tools/ts_deep2.sh "$BAM" SRR12044649_60 8 6 \
  2>&1 | tee -a "$WAITLOG"
echo "[$(date '+%F %T')] 全部结束" | tee -a "$WAITLOG"
