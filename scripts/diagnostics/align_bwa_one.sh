#!/usr/bin/env bash
# align_bwa_one.sh —— 用 bwa mem 做对照比对（同一份 FASTQ、同一参考、同一 markdup 流程）
# 目的：排除「Ts/Tv 偏低是 minimap2 造成的」这一可能
# 用法: bash align_bwa_one.sh <SRR> [输出后缀=bwa]
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

s="${1:?需要 SRR}"
SUF="${2:-bwa}"
DATA=/home/hugo/data
REF=$DATA/ref/ref_GCF_023101765.2.fna
RAW=$DATA/01_raw
ALN=$DATA/03_align
TMP=$DATA/tmp
THREADS=${THREADS:-10}

# FASTQ 输入选择：统一走 lib_select_fq.sh（不再用 `ls ... | head -1`）
# 旧写法有三个坑：字典序会选中数据最少的 .partial30；块文件 .partN 会被误选；
# 未裁尾的残片尾部有半条记录会让比对器崩。详见 lib_select_fq.sh 注释。
_libdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FQLIB="${FQLIB:-${_libdir}/lib_select_fq.sh}"
[ -f "$FQLIB" ] || { echo "[$s] FAIL 缺 FASTQ 选择库 $FQLIB"; exit 1; }
. "$FQLIB"
r1=$(pick_fq "${RAW}/${s}_1.fastq.gz")
r2=$(pick_fq "${RAW}/${s}_2.fastq.gz")
if [ -z "$r1" ] || [ -z "$r2" ]; then echo "[$s] SKIP 缺 FASTQ"; exit 0; fi
echo "[$s] 输入 R1=$(basename "$r1")  R2=$(basename "$r2")"
if [ -s "${ALN}/${s}.${SUF}.dedup.bam" ]; then echo "[$s] SKIP 已有 ${SUF} dedup.bam"; exit 0; fi

mkdir -p "$TMP"
tmpbam="${TMP}/${s}.${SUF}.bam"
echo "[$(date '+%T')] bwa mem 开始 线程=$THREADS"

bwa mem -t "$THREADS" -M \
  -R "@RG\tID:${s}\tSM:${s}\tPL:ILLUMINA\tLB:${s}\tPU:unit1" \
  "$REF" "$r1" "$r2" 2>/dev/null \
  | samtools sort -@ 2 -m 1G -T "${TMP}/${s}_bwas" -o "$tmpbam" -

[ -s "$tmpbam" ] || { echo "[$s] FAIL bwa 比对未产出"; rm -f "$tmpbam"; exit 1; }
echo "[$(date '+%T')] 去重中"

samtools collate -@ 2 -T "${TMP}/${s}_bwac" -o - "$tmpbam" \
  | samtools fixmate -@ 2 -m - - \
  | samtools sort -@ 2 -m 1G -T "${TMP}/${s}_bwamd" -o - - \
  | samtools markdup -@ 2 - "${ALN}/${s}.${SUF}.dedup.bam"
PS=("${PIPESTATUS[@]}")
if [ "${PS[0]:-0}" -ne 0 ] || [ "${PS[3]:-0}" -ne 0 ]; then
  echo "[$s] FAIL markdup 管道 (collate=${PS[0]:-?} markdup=${PS[3]:-?})"
  rm -f "${ALN}/${s}.${SUF}.dedup.bam"; exit 1
fi

samtools index -@ 2 "${ALN}/${s}.${SUF}.dedup.bam"
samtools flagstat -@ 2 "${ALN}/${s}.${SUF}.dedup.bam" > "${ALN}/${s}.${SUF}.flagstat"
rm -f "$tmpbam"
mm=$(awk '{m+=$3} END{print m+0}' <(samtools idxstats "${ALN}/${s}.${SUF}.dedup.bam"))
echo "[$(date '+%T')] DONE ${SUF} 比对上 reads=$mm"
grep -E 'in total|primary mapped \(|primary duplicates' "${ALN}/${s}.${SUF}.flagstat"
