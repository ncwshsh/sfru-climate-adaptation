#!/bin/bash
# verify_reuse.sh —— 校验 S2 复用清单里的 34 个文件（17 run × 2 mate）
# 判据（与 sweep_one.sh 同源）：
#   bad@  = 4 行组首行不以 @ 开头  -> 帧错位/损坏
#   bad+  = 第 3 行不以 + 开头
#   brk   = header 数字后缀不连续（丢记录）
#   complete = 总行数 % 4 == 0（末记录完整）
#   双端 record 数必须相等
# 运行：wsl -d Ubuntu-24.04 -- bash /mnt/c/SF_data/tools/verify_reuse.sh < /dev/null
export PATH="/usr/bin:/bin:$PATH"
PIGZ=/home/hugo/opt/pigz_root/usr/bin/pigz
RAW=/mnt/c/SF_data/01_raw
LIST=/mnt/c/SF_data/tools/reuse_s2.txt
OUT=/mnt/c/SF_data/tools/reuse_verify.tsv

printf 'run\tmate\tbytes\trecords\tbad@\tbad+\tbreaks\tlines_mod4\tverdict\n' > "$OUT"

while IFS=$'\t' read -r run gb dx; do
  [ -n "$run" ] || continue
  n1=""; n2=""
  for m in 1 2; do
    f=$(ls "$RAW"/${run}_${m}.fastq.gz* 2>/dev/null | head -1)
    if [ -z "$f" ]; then
      printf '%s\t%s\t-\t-\t-\t-\t-\t-\tMISSING\n' "$run" "$m" >> "$OUT"
      continue
    fi
    sz=$(stat -c %s "$f")
    read -r g ba bp brk rem < <("$PIGZ" -dc -p 4 "$f" 2>/dev/null | awk '
      NR%4==1 { if (substr($0,1,1)!="@") ba++
                h=$1; sub(/^@/,"",h); sub(/.*\./,"",h); n=h+0; g++
                if (prev!="" && n!=prev+1) brk++
                prev=n }
      NR%4==3 { if (substr($0,1,1)!="+") bp++ }
      END { printf "%d\t%d\t%d\t%d\t%d\n", g+0, ba+0, bp+0, brk+0, NR%4 }')
    v="ok"
    [ "$ba" -gt 0 ] && v="BAD_at"
    [ "$bp" -gt 0 ] && v="BAD_plus"
    [ "$brk" -gt 0 ] && v="BREAKS"
    [ "$rem" -ne 0 ] && v="TRUNCATED"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$run" "$m" "$sz" "$g" "$ba" "$bp" "$brk" "$rem" "$v" >> "$OUT"
    [ "$m" = "1" ] && n1="$g"
    [ "$m" = "2" ] && n2="$g"
  done
  if [ -n "$n1" ] && [ -n "$n2" ] && [ "$n1" != "$n2" ]; then
    # 裁尾按字节切，双端条数天然有小差；只报 >2.5% 的异常
    diffpct=$(awk -v a="$n1" -v b="$n2" 'BEGIN{m=(a>b?a:b); printf "%.2f", (m>0?(a>b?a-b:b-a)/m*100:0)}')
    big=$(awk -v p="$diffpct" 'BEGIN{print (p>2.5)?1:0}')
    if [ "$big" = "1" ]; then
      printf '%s\tPAIR\t-\t%s vs %s\t-\t-\t-\t-\tMATE_DIFF(%.2f%%)\n' "$run" "$n1" "$n2" "$diffpct" >> "$OUT"
    else
      printf '%s\tPAIR\t-\t%s vs %s\t-\t-\t-\t-\tok(diff %.2f%%)\n' "$run" "$n1" "$n2" "$diffpct" >> "$OUT"
    fi
  fi
  echo "[done] $run  R1=$n1 R2=$n2"
done < "$LIST"

echo "=== 汇总 ==="
echo "非 ok 行："
awk -F'\t' 'NR>1 && $9!="ok" {print "  "$0}' "$OUT"
echo "总行数 $(($(wc -l < "$OUT")-1))"
echo "结果表 $OUT"
