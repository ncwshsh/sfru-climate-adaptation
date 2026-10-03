#!/usr/bin/env bash
# run_kenya.sh —— 把已下好的肯尼亚 ≥20x 样本（SRR12044649，30% ≈ 22.9x）
# 搬进 WSL 原生盘并完成 minimap2 比对 + markdup + 索引。
# 在 WSL 内运行： wsl -d Ubuntu-24.04 -- bash /mnt/c/SF_data/tools/run_kenya.sh < /dev/null
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

S=SRR12044649
SRC=/mnt/c/SF_data/01_deep
DST=/home/hugo/data/01_raw
ALN=/home/hugo/data/03_align
LOG=${ALN}/${S}_run.log
mkdir -p "$ALN"

exec > >(tee -a "$LOG") 2>&1

echo "=== start $(date '+%F %T') ==="
df -h /home | tail -1

for m in 1 2; do
  f="${S}_${m}.fastq.gz.partial30"
  srcsz=$(stat -c%s "$SRC/$f" 2>/dev/null || echo 0)
  dstsz=$(stat -c%s "$DST/$f" 2>/dev/null || echo 0)
  if [ "$srcsz" = "0" ]; then echo "[ERR] 源文件缺失 $SRC/$f"; exit 1; fi
  if [ "$srcsz" != "$dstsz" ]; then
    echo "--- 拷贝 $f ($srcsz B) $(date '+%T') ---"
    t0=$(date +%s)
    cp "$SRC/$f" "$DST/$f.tmp" || { echo "[ERR] cp 失败"; exit 1; }
    mv "$DST/$f.tmp" "$DST/$f"
    t1=$(date +%s)
    echo "    耗时 $((t1-t0)) s  -> $(( srcsz / (t1-t0+1) / 1048576 )) MB/s"
  else
    echo "--- $f 已在位（$dstsz B）---"
  fi
  ls -l "$DST/$f"
done

echo "=== align $(date '+%F %T') ==="
THREADS=16 bash /mnt/c/SF_data/tools/align_mm2_one.sh "$S"
rc=$?

echo "=== 结果 $(date '+%F %T') rc=$rc ==="
ls -l "${ALN}/${S}".* 2>/dev/null
if [ -s "${ALN}/${S}.dedup.bam" ]; then
  echo "--- flagstat 摘要 ---"
  grep -E 'in total|primary mapped \(|primary duplicates' "${ALN}/${S}.flagstat"
  echo "--- 实测深度 ---"
  samtools idxstats "${ALN}/${S}.dedup.bam" | awk '
    {m+=$3; len+=$2}
    END{printf "参考总长 %d bp  已比对上 %d reads\n", len, m}'
  echo "--- avg read length ---"
  samtools view -F 0x904 "${ALN}/${S}.dedup.bam" 2>/dev/null | head -200000 \
    | awk '{n++; s+=length($10)} END{printf "%.1f bp (n=%d)\n", s/n, n}'
fi
echo "=== end $(date '+%F %T') ==="
