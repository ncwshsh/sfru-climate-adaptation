#!/usr/bin/env bash
# thin_beagle.sh —— 把 ANGSD 的 beagle 抽稀到 PCAngsd 吃得下的规模
#
# 为什么必须抽稀：
#   全量 16,230,602 个位点 × 214 个体 × 3 个基因型 × 8 字节 = 41.8 GB > 本机 23 GB
#   PCA 不需要这么多位点——结构信号在几十万个位点就已饱和，多的是冗余（且带来 LD 冗余）。
#   抽稀到 ~100 万位点 = 5.2 GB，安全且结果等价。
#
# ⚠️ 按固定间隔抽样（每 N 行取 1）而不是只取前 N 行：
#    只取前 N 行会全落在第一条染色体上，那是抽样偏差不是随机抽样。
#
# 用法: bash /mnt/c/SF_data/tools/thin_beagle.sh [间隔]
set -uo pipefail
export PATH=/home/hugo/mamba/envs/gea/bin:$PATH

IN=${IN:-/home/hugo/data/angsd/s2_gl.beagle.gz}
STEP=${1:-16}                 # 16,230,602 / 16 ≈ 1,014,000 位点
OUT=${OUT:-/home/hugo/data/angsd/beagle_1M.beagle.gz}

echo "===== $(date '+%F %T') 抽稀开始 每 ${STEP} 行取 1 ====="
echo "  输入: $IN ($(stat -c%s "$IN" | awk '{printf "%.2f GB", $1/1024^3}'))"

zcat "$IN" | awk -v s="$STEP" 'NR==1 {print; next} NR%s==0 {print}' | gzip -1c > "$OUT"

echo "===== $(date '+%F %T') 抽稀结束 ====="
echo "  输出: $OUT ($(stat -c%s "$OUT" | awk '{printf "%.2f GB", $1/1024^3}'))"
echo "  位点数: $(( $(zcat "$OUT" | wc -l) - 1 ))"
