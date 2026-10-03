#!/bin/bash
# sweep_one.sh —— 单文件结构扫描（供 xargs 并行调用）
# 用法: bash sweep_one.sh <fastq.gz>
export PATH="/usr/bin:/bin:$PATH"
PIGZ="${PIGZ:-$HOME/opt/pigz_root/usr/bin/pigz}"
f="$1"
[ -f "$f" ] || exit 0
D="$(dirname "$f")"; base="$(basename "$f")"

exp="NA"
# 凭证：统一为隐藏名 .nrec.<原名>（旧的非隐藏 X.nrec 会被 *.fastq.gz* 命中，已全部迁移，不再支持）
[ -f "$D/.nrec.$base" ] && exp="$(tr -d '[:space:]' < "$D/.nrec.$base")"

read -r g ba bp brk < <("$PIGZ" -dc -p 4 "$f" 2>/dev/null | awk '
  NR%4==1 {
    if (substr($0,1,1) != "@") ba++
    h=$1; sub(/^@/,"",h); sub(/.*\./,"",h); n=h+0
    g++
    if (prev != "" && n != prev+1) brk++
    prev=n
  }
  NR%4==3 { if (substr($0,1,1) != "+") bp++ }
  END { printf "%d\t%d\t%d\t%d\n", g+0, ba+0, bp+0, brk+0 }')

# 单次 printf，保证多进程追加时行不撕裂
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$base" "$exp" "$g" "$ba" "$bp" "$brk" >> /mnt/c/SF_data/tools/structure_sweep.tsv

flag=""
[ "${ba:-0}" -gt 0 ] && flag="${flag} bad@=$ba"
[ "${bp:-0}" -gt 0 ] && flag="${flag} bad+=$bp"
[ "${brk:-0}" -gt 0 ] && flag="${flag} breaks=$brk"
[ "$exp" != "NA" ] && [ "$exp" != "$g" ] && flag="${flag} 计数不符(凭证=$exp)"
if [ -n "$flag" ]; then echo "  [异常] $base$flag"; else echo "  [ok] $base  groups=$g"; fi
