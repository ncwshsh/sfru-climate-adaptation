#!/usr/bin/env bash
# screen_all.sh —— 全队列 220 样本抽样摸底：每样本抽 N 条 reads 用 bwa -k<K> 估比对率
# 目的：在决定正式比对参数前，先摸清每个样本的比对率分布（尤其 BR/FL 的问题规模）
# 输出: /mnt/c/SF_data/tools/screen_all.tsv  (SRR  module  mapped  total  rate_pct)
# 用法（WSL 内）: K=15 CONC=6 bash /mnt/c/SF_data/tools/screen_all.sh
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

TOOLS=/mnt/c/SF_data/tools
REF=/home/hugo/data/ref/ref_chr.fna
RAW=/mnt/c/SF_data/01_raw
T=/home/hugo/data/tmp
OUT=$TOOLS/screen_all.tsv
K=${K:-15}
CONC=${CONC:-6}
THREADS=${THREADS:-3}
LINES=${LINES:-400000}      # 每 mate 抽的行数 → LINES/4 条 reads

mkdir -p "$T"
printf "SRR\tmodule\tmapped\ttotal\trate_pct\n" > "$OUT"

screen_one() {
  local S="$1" MOD="$2"
  . "$TOOLS/lib_select_fq.sh"
  local r1 r2 n1
  r1=$(pick_fq "${RAW}/${S}_1.fastq.gz")
  [ -n "$r1" ] || return 0
  gzip -dc "$r1" 2>/dev/null | head -"$LINES" > "$T/${S}_s1.fq"
  n1=$(awk 'END{print NR/4}' "$T/${S}_s1.fq")

  local mp total
  if [ "$MOD" = "CN" ]; then
    mp=$(bwa mem -t "$THREADS" -k "$K" -p "$REF" "$T/${S}_s1.fq" 2>/dev/null | samtools view -c -F 2308 - 2>/dev/null)
    total=$n1
  else
    r2=$(pick_fq "${RAW}/${S}_2.fastq.gz")
    [ -n "$r2" ] || { rm -f "$T/${S}_s1.fq"; return 0; }
    gzip -dc "$r2" 2>/dev/null | head -"$LINES" > "$T/${S}_s2.fq"
    local n2; n2=$(awk 'END{print NR/4}' "$T/${S}_s2.fq")
    mp=$(bwa mem -t "$THREADS" -k "$K" "$REF" "$T/${S}_s1.fq" "$T/${S}_s2.fq" 2>/dev/null | samtools view -c -F 2308 - 2>/dev/null)
    total=$(( n1 + n2 ))
    rm -f "$T/${S}_s2.fq"
  fi
  rm -f "$T/${S}_s1.fq"
  local rate
  rate=$(awk -v a="${mp:-0}" -v b="${total:-0}" 'BEGIN{ if(b>0) printf "%.1f", a*100/b; else print "NA" }')
  printf "%s\t%s\t%s\t%s\t%s\n" "$S" "$MOD" "${mp:-0}" "$total" "$rate" >> "$OUT"
}
export -f screen_one
export TOOLS REF RAW T OUT K THREADS LINES

awk -F'\t' 'NR>1{print $1"\t"$3}' "$TOOLS/cohort_formal_s2.tsv" \
  | xargs -d '\n' -n 1 -P "$CONC" -I {} bash -c 'set -- {}; screen_one "$1" "$2"'

echo "--- 摸底完成 ---"
echo "  样本数: $(tail -n +2 "$OUT" | wc -l)"
awk -F'\t' 'NR>1{
  s+=$5; n++; if($5<mn||n==1)mn=$5; if($5>mx)mx=$5
  c[$2]++; r[$2]+=$5
} END{
  printf "  全队列: 均值 %.1f%%  范围 %.1f~%.1f%%\n", s/n, mn, mx
  for(m in c) printf "  %s: n=%d 均值 %.1f%%\n", m, c[m], r[m]/c[m]
}' "$OUT"
echo "--- 比对率 <70% 的样本（拟剔除/补救名单）---"
awk -F'\t' 'NR>1 && $5<70{printf "  %-14s %-3s %s%%\n",$1,$2,$5}' "$OUT" | sort -k3 -n
