#!/bin/bash
# sweep_structure.sh —— FASTQ 结构完整性全量扫描（比 gzip -t 强得多）
#
# 为什么需要它：gzip -t 只验证「压缩容器完整」，被帧错位污染的垃圾数据照样能通过。
#               实测 SRR18431710_2 就是这种：容器完整，尾部却是 4 行纯质量串。
#
# 三条判据（任一非零即异常）：
#   bad_at   : 4 行组的第 1 行不以 '@' 开头
#   bad_plus : 4 行组的第 3 行不以 '+' 开头
#   breaks   : header 里的读取序号未按 +1 递增（帧错位会立刻打破连续性）
export PATH="/usr/bin:/bin:$PATH"

PIGZ="${PIGZ:-$HOME/opt/pigz_root/usr/bin/pigz}"
OUT=/mnt/c/SF_data/tools/structure_sweep.tsv
DIRS="/mnt/c/SF_data/01_raw /mnt/c/SF_data/01_deep"

printf 'file\trec_expected\tgroups\tbad_at\tbad_plus\tseq_breaks\n' > "$OUT"

for D in $DIRS; do
  for f in "$D"/*.fastq.gz.partial[0-9] "$D"/*.fastq.gz.partial[0-9][0-9]; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    exp="NA"
    [ -f "$f.nrec" ] && exp="$(tr -d '[:space:]' < "$f.nrec")"
    [ -f "$D/.nrec.$base" ] && exp="$(tr -d '[:space:]' < "$D/.nrec.$base")"

    stat=$("$PIGZ" -dc -p 6 "$f" 2>/dev/null | awk '
      NR%4==1 {
        if (substr($0,1,1) != "@") ba++
        h=$1; sub(/^@/,"",h); sub(/.*\./,"",h); n=h+0
        g++
        if (prev != "" && n != prev+1) brk++
        prev=n
      }
      NR%4==3 { if (substr($0,1,1) != "+") bp++ }
      END { printf "%d\t%d\t%d\t%d", g+0, ba+0, bp+0, brk+0 }')

    printf '%s\t%s\t%s\n' "$base" "$exp" "$stat" >> "$OUT"
    printf '  %-42s %s  (凭证=%s)\n' "$base" "$stat" "$exp"
  done
done

echo
echo "================ 判定 ================"
awk -F'\t' 'NR>1 {
  if ($3+0>0 || $4+0>0 || $5+0>0) printf "  [结构异常] %-42s groups=%-10s bad@=%s bad+=%s breaks=%s\n", $1, $3, $4, $5, $6
}' "$OUT"
echo "  --- 记录数与凭证不符的 ---"
awk -F'\t' 'NR>1 && $2!="NA" && $2+0!=$3+0 {printf "  [计数不符] %-42s 凭证=%s 实扫=%s\n", $1, $2, $3}' "$OUT"
echo
echo "  扫描条目 = $(( $(wc -l < "$OUT") - 1 ))"
echo "=== sweep done ==="
