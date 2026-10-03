#!/usr/bin/env bash
# dl_then_trim.sh —— 下载 + 快速裁尾（两段式：Git Bash 下载 → WSL pigz 裁尾）
#
# 为什么必须两段式：
#   `dl_ena.sh` 内建的裁尾跑在 Git Bash 侧，压缩器是**单线程 gzip**，
#   实测裁尾产出仅 **2.98 MB/s**（3.34 GB 的 R1 要 ~19 分钟，R2 还要更久）。
#   而 `heal_one.sh` 在 WSL 内用 pigz 直接读文件，历史实测 **~30 MB/s**（53 文件 / 74 GB / 42 min）→ 快约 10×。
#
#   ⚠️ 不要试图用 `ZIP="wsl -d Ubuntu-24.04 -- /home/hugo/opt/pigz_root/usr/bin/pigz -p 8"` 走管道：
#      实测跨 Git Bash↔WSL 边界管道只有 14 MB/s，比本机 gzip 的 33 MB/s 还慢。
#
# 幂等：裁尾成功后 heal_one.sh 写隐藏凭证 .nrec.<原名> → 重跑本脚本会跳过
#
# 用法: bash dl_then_trim.sh <SRR> <PCT> [并发=8] [块MB=16]
set -uo pipefail
export PATH="/usr/bin:/bin:$PATH"

SRR="${1:?需要 SRR}"
PCT="${2:?需要 PCT}"
W="${3:-8}"
BS="${4:-16}"
OUT_WIN=C:/SF_data/01_raw
OUT_POSIX=/c/SF_data/01_raw
T=/c/SF_data/tools
SUF=""
[ "$PCT" != "100" ] && SUF=".partial${PCT}"

echo "=== 步骤 1/2：下载（TRIM=0，不裁尾）==="
TRIM=0 bash "$T/dl_ena.sh" "$SRR" "$W" "$BS" "$OUT_WIN" "$PCT"
rc=$?
[ "$rc" -ne 0 ] && echo "[WARN] dl_ena.sh 退出码=$rc（可能有块未完成；仍尝试对已存在的文件裁尾）"

echo
echo "=== 步骤 2/2：WSL pigz 裁尾（~30 MB/s，比内建 gzip 快约 10×）==="
for m in 1 2; do
  base="${SRR}_${m}.fastq.gz${SUF}"
  f="${OUT_POSIX}/${base}"
  if [ ! -f "$f" ]; then echo "  [跳过] 缺 ${base}"; continue; fi
  if [ -f "${OUT_POSIX}/.nrec.${base}" ]; then echo "  [跳过] ${base} 已有裁剪凭证"; continue; fi
  wsl -d Ubuntu-24.04 -- bash /mnt/c/SF_data/tools/heal_one.sh "/mnt/c/SF_data/01_raw/${base}" < /dev/null
done

echo
echo "=== 完成。产物 ==="
ls -la ${OUT_POSIX}/${SRR}_*.fastq.gz${SUF} 2>/dev/null
ls -la ${OUT_POSIX}/.nrec.${SRR}_*.fastq.gz${SUF} 2>/dev/null
