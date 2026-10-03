#!/bin/bash
# verify_heal.sh —— 裁尾后全面体检
# 判据一：双端记录数应基本相等（同一文库 R1/R2 spot 数一致，差异 <1% 正常）
# 判据二：读长应合理（Illumina 150/151 bp；长读平台则上万 bp）
# 判据三：每个文件都必须能通过 pigz -t（完整 gzip 容器）
export PATH="/usr/bin:/bin:$PATH"
PIGZ="${PIGZ:-$HOME/opt/pigz_root/usr/bin/pigz}"
OUT=/mnt/c/SF_data/tools/verify_heal.tsv
DIRS="/mnt/c/SF_data/01_raw /mnt/c/SF_data/01_deep"

printf 'file\trecords\tbytes\treadlen\tmate\trec_mate\tmismatch_pct\n' > "$OUT"

# 第一遍：收集所有凭证里的记录数（key = 目录/基础名）
declare -A REC
for D in $DIRS; do
  for mk in "$D"/*.nrec; do
    [ -f "$mk" ] || continue
    b="$(basename "$mk")"; base="${b%.nrec}"
    REC["$D/$base"]="$(tr -d '[:space:]' < "$mk")"
  done
done

# 第二遍：逐文件测读长 + gzip 完整性 + 找 mate
for D in $DIRS; do
  for f in "$D"/*.fastq.gz.partial[0-9] "$D"/*.fastq.gz.partial[0-9][0-9]; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    rec="${REC["$D/$base"]:-NA}"

    if "$PIGZ" -t -p 8 "$f" 2>/dev/null; then gz="ok"; else gz="BAD"; fi

    rl=$("$PIGZ" -dc -p 4 "$f" 2>/dev/null | head -4 | awk 'NR==2{print length($0)}')
    sz=$(stat -c %s "$f")

    # 推 mate
    case "$base" in
      *_1.fastq.gz.partial*) mate="${base/_1.fastq.gz.partial/_2.fastq.gz.partial}" ;;
      *_2.fastq.gz.partial*) mate="${base/_2.fastq.gz.partial/_1.fastq.gz.partial}" ;;
      *) mate="" ;;
    esac
    mrec="NA"
    if [ -n "$mate" ] && [ -n "${REC["$D/$mate"]:-}" ]; then mrec="${REC["$D/$mate"]}"; fi

    mm="NA"
    if [ "$rec" != "NA" ] && [ "$mrec" != "NA" ]; then
      mm=$(awk -v a="$rec" -v b="$mrec" 'BEGIN{d=(a-b); if(d<0)d=-d; m=(a>b?a:b); printf "%.2f", (m>0? 100*d/m : 0)}')
    fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$base" "$rec" "$sz" "$rl" "$mate" "$mrec" "$mm" >> "$OUT"
    [ "$gz" = "BAD" ] && echo "  [gzip BAD] $base"
  done
done

echo "=== 双端记录数不一致 >5% 的样本（高度可疑）==="
awk -F'\t' 'NR>1 && $7!="NA" && $7+0>5 {printf "  %-38s rec=%-10s  mate rec=%-10s  差 %s%%\n", $1, $2, $6, $7}' "$OUT"
echo
echo "=== 读长分布 ==="
awk -F'\t' 'NR>1{print $4}' "$OUT" | sort -n | uniq -c
echo
echo "=== 无 mate 的条目 ==="
awk -F'\t' 'NR>1 && $6=="NA" {printf "  %-38s rec=%s readlen=%s\n", $1, $2, $4}' "$OUT"
echo
echo "=== 汇总 ==="
echo "  体检条目      = $(( $(wc -l < "$OUT") - 1 ))"
echo "  gzip 全通过   = $(awk -F'\t' 'NR>1' "$OUT" | wc -l) 个（上面未打印 BAD 即为全通过）"
echo "  台账: $OUT"
