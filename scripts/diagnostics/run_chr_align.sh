#!/usr/bin/env bash
# run_chr_align.sh —— 用 ref_chr（31 条核染色体）做重比对
#
# 为什么需要这个脚本：
#   1) 现有全部 BAM 都建在**全量参考** ref_GCF_023101765.2.fna 上 —— 它含 37 条 NW_ scaffold
#      + 1 条线粒体(NC_027836.1)。scaffold 只占基因组 0.56% 碱基却吃掉 6.1% reads
#      （NW_026095720.1 仅 44 kb 却塌缩到 8,409×）→ 必须剔除。
#   2) ref_chr.fna 已于 2026-09-17 02:21 建好（31 条 / 381,761,283 bp，已自检），
#      但**此前没有任何比对脚本引用它** —— 本脚本补上这个缺口。
#
# 用法:
#   wsl -d Ubuntu-24.04 -- bash /mnt/c/SF_data/tools/run_chr_align.sh \
#        <SRR> <TAG> <R1> <R2> < /dev/null
# 例:
#   wsl -d Ubuntu-24.04 -- bash /mnt/c/SF_data/tools/run_chr_align.sh \
#        SRR12044649 60chr \
#        /home/hugo/data/01_raw/clean/SRR12044649_1.60clean.fq.gz \
#        /home/hugo/data/01_raw/clean/SRR12044649_2.60clean.fq.gz < /dev/null
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

S="${1:?需要 SRR}"
TAG="${2:?需要 TAG（如 60chr）}"
R1="${3:?需要 R1 路径}"
R2="${4:?需要 R2 路径}"

REF=/home/hugo/data/ref/ref_chr.fna
MMI=${REF}.mmi
ALN=/home/hugo/data/03_align
TMP=/home/hugo/data/tmp
THREADS=${THREADS:-10}
OUTBAM="${ALN}/${S}_${TAG}.dedup.bam"
LOG="${ALN}/${S}_${TAG}_run.log"
mkdir -p "$ALN" "$TMP"

[ -s "$MMI" ] || { echo "[ERR] 缺 ref_chr 索引 $MMI"; exit 1; }
[ -s "${REF}.fai" ] || { echo "[ERR] 缺 ${REF}.fai"; exit 1; }
[ -s "$R1" ] || { echo "[ERR] 缺 R1: $R1"; exit 1; }
[ -s "$R2" ] || { echo "[ERR] 缺 R2: $R2"; exit 1; }

exec > >(tee -a "$LOG") 2>&1
echo "=== start $(date '+%F %T') | 参考=$(basename "$REF") | 线程=$THREADS ==="
echo "输入: $(basename "$R1")  |  $(basename "$R2")"

# ---- 参考自检：必须恰好 31 条，且不含 scaffold / 线粒体 ----
nseq=$(wc -l < "${REF}.fai")
nnw=$(grep -c '^NW_' "${REF}.fai" || true)
nmt=$(grep -c '^NC_027836' "${REF}.fai" || true)
echo "--- 参考自检 ---"
echo "  序列数 = ${nseq}（应为 31）｜ NW_ scaffold = ${nnw}（应为 0）｜ 线粒体 NC_027836 = ${nmt}（应为 0）"
if [ "$nseq" != "31" ] || [ "$nnw" != "0" ] || [ "$nmt" != "0" ]; then
  echo "[FATAL] 参考不是纯 31 条核染色体，拒绝继续"; exit 1
fi

echo "--- minimap2 sr 比对 $(date '+%T') ---"
minimap2 -ax sr -t "$THREADS" \
  -R "@RG\tID:${S}\tSM:${S}\tPL:ILLUMINA\tLB:${S}\tPU:unit1" \
  "$MMI" "$R1" "$R2" 2>/dev/null \
  | samtools sort -@ 4 -m 1G -T "${TMP}/${S}${TAG}_s" -o "${TMP}/${S}${TAG}.bam" -
[ -s "${TMP}/${S}${TAG}.bam" ] || { echo "[ERR] 比对未产出（minimap2 崩？看上方 stderr 已丢弃，或内存不足）"; exit 1; }

echo "--- collate/fixmate/sort/markdup $(date '+%T') ---"
samtools collate -@ 4 -T "${TMP}/${S}${TAG}_c" -o - "${TMP}/${S}${TAG}.bam" \
  | samtools fixmate -@ 4 -m - - \
  | samtools sort -@ 4 -m 1G -T "${TMP}/${S}${TAG}_md" -o - - \
  | samtools markdup -@ 4 - "$OUTBAM"
PS=("${PIPESTATUS[@]}")
if [ "${PS[0]:-0}" -ne 0 ] || [ "${PS[3]:-0}" -ne 0 ]; then
  echo "[ERR] markdup 管道出错 collate=${PS[0]:-?} markdup=${PS[3]:-?}"; rm -f "$OUTBAM"; exit 1
fi

samtools index -@ 4 "$OUTBAM"
samtools flagstat -@ 4 "$OUTBAM" > "${ALN}/${S}_${TAG}.flagstat"
rm -f "${TMP}/${S}${TAG}.bam"

echo "=== 结果 $(date '+%F %T') ==="
grep -E 'in total|primary mapped \(|primary duplicates' "${ALN}/${S}_${TAG}.flagstat"
echo "--- 染色体 raw 深度 ---"
samtools idxstats "$OUTBAM" | awk '$2>1000000{m+=$3; l+=$2; n++} END{printf "  raw 深度 = %.2f x （%d 条 / %d bp）\n", m*151/l, n, l}'
echo "--- 比对到非染色体序列的残留（应为空）---"
samtools idxstats "$OUTBAM" | awk '$1!="*" && $1 !~ /^NC_0642/ {print "  [异常] "$1" reads="$3}'
echo "=== end ==="
