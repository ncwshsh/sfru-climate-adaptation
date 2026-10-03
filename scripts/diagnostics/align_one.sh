#!/usr/bin/env bash
# align_one.sh —— 单样本比对（供 align_parallel.sh 用 xargs -P 并发调用）
# 用法: bash align_one.sh <SRR>
set -u
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
eval "$(/mnt/c/SF_data/tools/micromamba shell hook -s bash)"
micromamba activate sfru

s="$1"
REF=/mnt/c/SF_data/03_align/ref_GCF_023101765.2.fna
RAW=/mnt/c/SF_data/01_raw
ALN=/mnt/c/SF_data/03_align
TMP=/mnt/c/SF_data/tmp
THREADS=${THREADS:-4}

# 找 FASTQ：统一走 lib_select_fq.sh（不再用 `ls ... | head -1`）
# 旧写法有三个坑：字典序会选中数据最少的 .partial30；块文件 .partN 会被误选；
# 未裁尾的残片尾部有半条记录会让比对器崩。详见 lib_select_fq.sh 注释。
_libdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FQLIB="${FQLIB:-${_libdir}/lib_select_fq.sh}"
[ -f "$FQLIB" ] || { echo "[$s] FAIL 缺 FASTQ 选择库 $FQLIB"; exit 1; }
. "$FQLIB"
r1=$(pick_fq "${RAW}/${s}_1.fastq.gz")
r2=$(pick_fq "${RAW}/${s}_2.fastq.gz")
if [ -z "$r1" ] || [ -z "$r2" ]; then
  echo "[$s] SKIP 缺 FASTQ"
  exit 0
fi
echo "[$s] 输入 R1=$(basename "$r1")  R2=$(basename "$r2")"
if [ -s "${ALN}/${s}.dedup.bam" ]; then
  echo "[$s] SKIP 已有 dedup.bam"
  exit 0
fi

mkdir -p "$TMP"
tmpbam="${TMP}/${s}.bam"

bwa mem -t "$THREADS" -M \
  -R "@RG\tID:${s}\tSM:${s}\tPL:ILLUMINA\tLB:${s}\tPU:unit1" \
  "$REF" "$r1" "$r2" 2>/dev/null \
  | samtools sort -@ 2 -m 1G -T "${TMP}/${s}_s" -o "$tmpbam" -

if [ ! -s "$tmpbam" ]; then
  echo "[$s] FAIL 比对未产出"
  rm -f "$tmpbam"
  exit 1
fi

# 去重：collate -> fixmate -> sort -> markdup
samtools collate -@ 2 -O -T "${TMP}/${s}_c" -o - "$tmpbam" \
  | samtools fixmate -@ 2 -m - - \
  | samtools sort -@ 2 -m 1G -T "${TMP}/${s}_md" -o - - \
  | samtools markdup -@ 2 - "${ALN}/${s}.dedup.bam"

samtools index -@ 2 "${ALN}/${s}.dedup.bam"
samtools flagstat -@ 2 "${ALN}/${s}.dedup.bam" > "${ALN}/${s}.flagstat"
mapped=$(grep -m1 'mapped (' "${ALN}/${s}.flagstat" | awk '{print $1}')
rate=$(grep -m1 'mapped (' "${ALN}/${s}.flagstat" | sed 's/.*(\([0-9.]*%\).*/\1/')

rm -f "$tmpbam"
echo "[$s] DONE ${mapped} mapped ${rate}"
