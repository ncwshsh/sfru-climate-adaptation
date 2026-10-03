#!/usr/bin/env bash
# run60b.sh —— 重跑 60% 比对：先生成完整记录边界的干净 FASTQ，再比对
# 前置：末尾半条记录导致 minimap2 崩（见 make_clean60.sh 头注释）
export PATH=/home/hugo/mamba/envs/sfru/bin:/usr/bin:/bin:$PATH

echo "=== 步骤 1/2：截到完整记录边界 ==="
bash /mnt/c/SF_data/tools/make_clean60.sh || { echo "[FATAL] 干净化失败"; exit 1; }

echo
echo "=== 步骤 2/2：重新比对 60%（日志追加到 SRR12044649_60_run.log）==="
bash /mnt/c/SF_data/tools/run_kenya60.sh
echo "[run60b] 退出码=$?"
