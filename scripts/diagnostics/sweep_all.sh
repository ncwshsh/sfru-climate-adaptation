#!/bin/bash
# sweep_all.sh —— 结构完整性全量扫描（并行驱动）
# 判据（任一非零即异常）：第1行非@ / 第3行非+ / 读取序号不连续
export PATH="/usr/bin:/bin:$PATH"

OUT=/mnt/c/SF_data/tools/structure_sweep.tsv
LIST=/mnt/c/SF_data/tools/sweep_list.txt
LOG=/mnt/c/SF_data/tools/sweep_run.log
DIRS="/mnt/c/SF_data/01_raw /mnt/c/SF_data/01_deep"
PAR="${PAR:-3}"

printf 'file\trec_expected\tgroups\tbad_at\tbad_plus\tseq_breaks\n' > "$OUT"
: > "$LIST"
for D in $DIRS; do
  for f in "$D"/*.fastq.gz.partial[0-9] "$D"/*.fastq.gz.partial[0-9][0-9]; do
    [ -f "$f" ] || continue
    echo "$f" >> "$LIST"
  done
done
n=$(grep -c . "$LIST")
echo "[$(date +%H:%M:%S)] 结构扫描 $n 个文件，并发 $PAR" | tee -a "$LOG"

xargs -d '\n' -r -P "$PAR" -n 1 bash /mnt/c/SF_data/tools/sweep_one.sh < "$LIST" 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "[$(date +%H:%M:%S)] ======== 判定 ========" | tee -a "$LOG"
awk -F'\t' 'NR>1 { if ($4+0>0 || $5+0>0 || $6+0>0) printf "  [结构异常] %-42s groups=%s bad@=%s bad+=%s breaks=%s\n", $1, $3, $4, $5, $6 }' "$OUT" | tee -a "$LOG"
awk -F'\t' 'NR>1 && $2!="NA" && $2+0!=$3+0 { printf "  [计数不符] %-42s 凭证=%s 实扫=%s\n", $1, $2, $3 }' "$OUT" | tee -a "$LOG"
echo "  扫描条目 = $(( $(wc -l < "$OUT") - 1 ))" | tee -a "$LOG"
echo "  总记录数 = $(awk -F'\t' 'NR>1{s+=$3} END{printf "%.0f", s}' "$OUT")" | tee -a "$LOG"
echo "=== sweep done ===" | tee -a "$LOG"
