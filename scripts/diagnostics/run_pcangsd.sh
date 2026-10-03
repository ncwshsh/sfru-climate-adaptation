#!/usr/bin/env bash
# run_pcangsd.sh —— 用 PCAngsd 从基因型似然直接算群体结构（不先硬叫基因型）
#
# 为什么用 PCAngsd 而不是"先 call 变异再 PCA"：
#   本队列 ~6x，基因型不确定度大。PCAngsd 直接吃 ANGSD 的似然，把不确定度带进协方差矩阵，
#   避免"深度越低 → 越像纯合 → 越像祖先类型"这类假结构。
#
# 输入：抽稀后的 beagle（见 thin_beagle.sh）
# 输出：*.cov（协方差矩阵）、*.cpos（位点坐标）、*.log
set -uo pipefail
export PATH=/home/hugo/mamba/envs/gea/bin:$PATH

BEAGLE=${BEAGLE:-/home/hugo/data/angsd/beagle_1M.beagle.gz}
OUT=${OUT:-/home/hugo/data/angsd/pca_s2}
EIG=${EIG:-20}
THR=${THR:-20}

echo "===== $(date '+%F %T') PCAngsd 开始 ====="
echo "  输入: $BEAGLE"
echo "  特征向量数: $EIG   线程: $THR"
# ★ 必须加大 --iter（**不是 --maf-iter**）：
#   日志里 "Individual allele frequencies estimated (101)" 这一轮受 --iter 控制，默认只有 100 次，
#   本队列跑到 101 次时 RMSE 仍有 3.27e-4，且每轮只降约 2.5%，PCAngsd 会报 "did not converge"。
#   按此速率降到 1e-6 大约还要 230 轮 ⇒ 给 500 轮（约 20~25 分钟）。
#   ⚠️ 试过 --maf-iter 300，无效——它管的是另一层（次等位频率）迭代。
/usr/bin/time -f "  耗时 %e s  峰值内存 %M KB" \
  pcangsd -b "$BEAGLE" -e "$EIG" -t "$THR" --iter "${ITER:-500}" --tole "${TOLE:-1e-6}" -o "$OUT" 2>&1 | tail -20
echo "===== $(date '+%F %T') PCAngsd 结束 ====="
ls -la "$OUT".* 2>/dev/null
