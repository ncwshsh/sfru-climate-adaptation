#!/usr/bin/env bash
# make_clean60.sh —— 把 partial60 的 FASTQ 截到完整记录边界，产出可直接比对的干净文件
#
# 背景：dl_ena.sh 按 16MB 块拼前缀，切口落在记录中间 -> 末尾出现半条记录
#   实测 R1 = 59,116,181 条完整记录 + 1 个断头 header
#        R2 = 59,475,634 条完整记录 + header + 148bp 残缺 SEQ（无 QUAL）
#   -> minimap2 报 [E::sam_parse1] SEQ and QUAL are of different length
#
# 修法：两边都只取前 N = min(两者) 条完整记录，用 head -n N*4 精确截取
#   （head 读够即退出，zcat 收 SIGPIPE，所以本脚本不能开 pipefail；
#     输出行数由 head -n 保证恰为 N*4，无需全量复核，只查末条记录）
export PATH=/home/hugo/mamba/envs/sfru/bin:/usr/bin:/bin:$PATH

N=59116181                    # R1 与 R2 的完整记录数取小
SRC=/home/hugo/data/01_raw
DST=/home/hugo/data/01_raw/clean
mkdir -p "$DST"

ZIP="gzip"
command -v pigz >/dev/null 2>&1 && ZIP="pigz -p 6"

for m in 1 2; do
  src="$SRC/SRR12044649_${m}.fastq.gz.partial60"
  dst="$DST/SRR12044649_${m}.60clean.fq.gz"
  [ -s "$src" ] || { echo "[ERR] 缺 $src"; exit 1; }
  if [ -s "$dst" ]; then
    echo "[skip] $dst 已存在（$(stat -c%s "$dst") B）"
  else
    echo "--- 生成 $(basename "$dst")  取前 $N 条记录 ---"
    t0=$(date +%s)
    zcat "$src" 2>/dev/null | head -n $((N*4)) | $ZIP > "$dst"
    t1=$(date +%s)
    echo "    完成 耗时 $((t1-t0))s  体积 $(stat -c%s "$dst") B"
  fi
done

echo
echo "########## 校验末条记录（应为 header/SEQ/+/QUAL，SEQ 与 QUAL 等长）##########"
for m in 1 2; do
  f="$DST/SRR12044649_${m}.60clean.fq.gz"
  echo "--- $(basename "$f") ---"
  zcat "$f" 2>/dev/null | tail -4 | awk '{printf "  len=%-4d %s\n", length($0), substr($0,1,58)}'
done
