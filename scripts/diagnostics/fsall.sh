#!/usr/bin/env bash
# fsall.sh —— 对比若干 BAM 的 flagstat（重复率）
set -uo pipefail
D=/home/hugo/data/03_align
for n in "$@"; do
  f="$D/$n"
  if [ -s "$f" ]; then
    tot=$(grep -m1 'in total' "$f" | awk '{print $1}')
    dup=$(grep -m1 'primary duplicates' "$f" | awk '{print $1}')
    map=$(grep -m1 'primary mapped (' "$f" | awk '{print $1}')
    sup=$(grep -m1 'supplementary' "$f" | awk '{print $1}')
    awk -v n="$n" -v t="$tot" -v d="$dup" -v m="$map" -v s="$sup" \
      'BEGIN{printf "%-28s total=%-10d 重复=%-10d (%.1f%%)  mapped=%-10d (%.1f%%)  supp=%d\n", n, t, d, 100*d/t, m, 100*m/t, s}'
  else
    echo "$n  (无 flagstat)"
  fi
done
