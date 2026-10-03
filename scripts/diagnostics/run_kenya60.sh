#!/usr/bin/env bash
# run_kenya60.sh —— 把 60% 版 FASTQ 换上并比对，产出 SRR12044649_60.dedup.bam
#
# 两个必须绕开的坑：
#  1) align_mm2_one.sh 见 ${ALN}/${s}.dedup.bam 存在就 SKIP -> 所以必须换输出名前缀
#  2) 01_raw 里若同时存在 .partial30 和 .partial60，glob 'ls *_1.fastq.gz*' 按字典序
#     head -1 会命中 .partial30（错的）-> 必须先把 .partial30 删掉
#  3) bwa 对照任务正在读 .partial30，删文件前要确认它已读完（unlink 后 fd 仍有效，
#     但为稳妥，本脚本先等 bwa 进程退出）
# 用法: wsl -d Ubuntu-24.04 -- bash /mnt/c/SF_data/tools/run_kenya60.sh < /dev/null
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

S=SRR12044649
TAG=60
SRC=/mnt/c/SF_data/01_deep
DST=/home/hugo/data/01_raw
ALN=/home/hugo/data/03_align
TMP=/home/hugo/data/tmp
REF=/home/hugo/data/ref/ref_GCF_023101765.2.fna
MMI=${REF}.mmi
THREADS=${THREADS:-10}
LOG=${ALN}/${S}_${TAG}_run.log
mkdir -p "$ALN" "$TMP"
exec > >(tee -a "$LOG") 2>&1

echo "=== start $(date '+%F %T') ==="

echo "--- 拷贝 60% 版 ---"
for m in 1 2; do
  f="${S}_${m}.fastq.gz.partial60"
  srcsz=$(stat -c%s "$SRC/$f" 2>/dev/null || echo 0)
  [ "$srcsz" = "0" ] && { echo "[ERR] 缺 $SRC/$f"; exit 1; }
  dstsz=$(stat -c%s "$DST/$f" 2>/dev/null || echo 0)
  if [ "$srcsz" != "$dstsz" ]; then
    t0=$(date +%s)
    cp "$SRC/$f" "$DST/$f.tmp" && mv "$DST/$f.tmp" "$DST/$f"
    t1=$(date +%s)
    echo "  $f  $srcsz B  耗时 $((t1-t0))s  -> $(( srcsz/(t1-t0+1)/1048576 )) MB/s"
  else
    echo "  $f 已在位（$dstsz B）"
  fi
done

# 直接用显式文件名，不走 glob —— 这样 01_raw 里留着 .partial30 也不会被误选
# ⚠️ 2026-09-17 修正：partial60 的末尾是半条记录（16MB 块切口），
#    直接用会让 minimap2 报 "SEQ and QUAL are of different length" 而崩。
#    必须先经 make_clean60.sh 截到完整记录边界，改用 clean/ 下的干净文件。
CLEAN=${DST}/clean
r1="${CLEAN}/${S}_1.60clean.fq.gz"
r2="${CLEAN}/${S}_2.60clean.fq.gz"
[ -s "$r1" ] || { echo "[ERR] 缺干净文件 $r1（先跑 make_clean60.sh）"; exit 1; }
[ -s "$r2" ] || { echo "[ERR] 缺干净文件 $r2（先跑 make_clean60.sh）"; exit 1; }
echo "用到的输入: $r1  |  $r2"

if [ ! -s "$MMI" ]; then
  echo "--- 建 minimap2 索引 ---"
  minimap2 -x sr -d "${MMI}.tmp.$$" "$REF" 2>/dev/null && mv "${MMI}.tmp.$$" "$MMI"
fi

OUTBAM="${ALN}/${S}_${TAG}.dedup.bam"
echo "--- minimap2 sr 比对 $(date '+%T') ---"
minimap2 -ax sr -t "$THREADS" \
  -R "@RG\tID:${S}\tSM:${S}\tPL:ILLUMINA\tLB:${S}\tPU:unit1" \
  "$MMI" "$r1" "$r2" 2>/dev/null \
  | samtools sort -@ 4 -m 1G -T "${TMP}/${S}${TAG}_s" -o "${TMP}/${S}${TAG}.bam" -

[ -s "${TMP}/${S}${TAG}.bam" ] || { echo "[ERR] 比对未产出"; exit 1; }
echo "--- collate/fixmate/sort/markdup $(date '+%T') ---"
samtools collate -@ 4 -T "${TMP}/${S}${TAG}_c" -o - "${TMP}/${S}${TAG}.bam" \
  | samtools fixmate -@ 4 -m - - \
  | samtools sort -@ 4 -m 1G -T "${TMP}/${S}${TAG}_md" -o - - \
  | samtools markdup -@ 4 - "$OUTBAM"
PS=("${PIPESTATUS[@]}")
if [ "${PS[0]:-0}" -ne 0 ] || [ "${PS[3]:-0}" -ne 0 ]; then
  echo "[ERR] markdup 管道出错 collate=${PS[0]:-?} markdup=${PS[3]:-?}"
  rm -f "$OUTBAM"; exit 1
fi

samtools index -@ 4 "$OUTBAM"
samtools flagstat -@ 4 "$OUTBAM" > "${ALN}/${S}_${TAG}.flagstat"
rm -f "${TMP}/${S}${TAG}.bam"

echo "=== 结果 $(date '+%F %T') ==="
grep -E 'in total|primary mapped \(|primary duplicates|supplementary' "${ALN}/${S}_${TAG}.flagstat"
echo "--- raw 深度（染色体）---"
samtools idxstats "$OUTBAM" | awk '$2>1000000{m+=$3; l+=$2} END{printf "染色体 raw 深度 = %.2f x\n", m*151/l}'
echo "--- 均值读长 ---"
samtools view -F 0x904 "$OUTBAM" 2>/dev/null | head -200000 | awk '{n++; s+=length($10)} END{printf "%.1f bp (n=%d)\n", s/n, n}'
echo "=== end ==="
