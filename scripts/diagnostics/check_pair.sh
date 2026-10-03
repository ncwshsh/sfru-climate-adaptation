#!/usr/bin/env bash
# check_pair.sh —— 诊断双端配对是否同步（截断下载可能让 R1/R2 reads 数不等）
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
RAW=/home/hugo/data/01_raw

# FASTQ 输入选择：统一走 lib_select_fq.sh（不再用 `ls ... | head -1`）
_libdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FQLIB="${FQLIB:-${_libdir}/lib_select_fq.sh}"
[ -f "$FQLIB" ] || { echo "[ERR] 缺 FASTQ 选择库 $FQLIB"; exit 1; }
. "$FQLIB"

echo "=== flagstat 全文 ==="
for f in /home/hugo/data/03_align/*.flagstat; do
  echo "-- $(basename "$f")"
  cat "$f"
done

echo
echo "=== 双端 reads 数是否同步（各取 2 个样本测）==="
for s in SRR10980085 SRR11528381; do
  r1=$(pick_fq "${RAW}/${s}_1.fastq.gz")
  r2=$(pick_fq "${RAW}/${s}_2.fastq.gz")
  echo "[$s]"
  echo "  R1 = $r1"
  echo "  R2 = $r2"
  n1=$(pigz -dc "$r1" 2>/dev/null | wc -l)
  n2=$(pigz -dc "$r2" 2>/dev/null | wc -l)
  echo "  R1 reads = $((n1/4))"
  echo "  R2 reads = $((n2/4))"
  echo "  差值     = $(( n1/4 - n2/4 ))"
done

echo
echo "=== R1/R2 前 4 条 read ID 对照（必须完全一致）==="
for s in SRR10980085; do
  r1=$(pick_fq "${RAW}/${s}_1.fastq.gz")
  r2=$(pick_fq "${RAW}/${s}_2.fastq.gz")
  echo "-- $s R1 --"; pigz -dc "$r1" 2>/dev/null | head -8 | awk 'NR%4==1'
  echo "-- $s R2 --"; pigz -dc "$r2" 2>/dev/null | head -8 | awk 'NR%4==1'
done
