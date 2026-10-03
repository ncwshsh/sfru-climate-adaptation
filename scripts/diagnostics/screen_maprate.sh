#!/usr/bin/env bash
# screen_maprate.sh —— 抽样快速估计比对率（每样本只比 10 万条，约 1 分钟）
# 目的：在决定「是否全队列改 -k15」之前，先摸清各模块（尤其 US 主力 143 个）的比对率分布
# 用法（WSL 内）: bash /mnt/c/SF_data/tools/screen_maprate.sh
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
REF=/home/hugo/data/ref/ref_chr.fna
T=/home/hugo/data/tmp
RAW=/mnt/c/SF_data/01_raw
OUT=/mnt/c/SF_data/tools/screen_maprate.tsv
K=${K:-19}
THREADS=${THREADS:-4}
LINES=${LINES:-400000}   # 每 mate 抽的行数（= LINES/4 条 reads）

mkdir -p "$T"
printf "SRR\tmodule\tmapped\ttotal\trate_pct\n" > "$OUT"

screen_one() {
  local S="$1" MOD="$2"
  local r1 r2
  # 用 lib_select_fq.sh 选输入
  . /mnt/c/SF_data/tools/lib_select_fq.sh
  r1=$(pick_fq "${RAW}/${S}_1.fastq.gz")
  if [ "$MOD" = "CN" ]; then r2=""; else r2=$(pick_fq "${RAW}/${S}_2.fastq.gz"); fi
  [ -n "$r1" ] || return 0

  gzip -dc "$r1" 2>/dev/null | head -"$LINES" > "$T/${S}_sc1.fq"
  if [ -n "$r2" ]; then
    gzip -dc "$r2" 2>/dev/null | head -"$LINES" > "$T/${S}_sc2.fq"
  else
    : > "$T/${S}_sc2.fq"
  fi

  local tot mp
  if [ "$MOD" = "CN" ]; then
    tot=$(bwa mem -t "$THREADS" -k "$K" -p "$REF" "$T/${S}_sc1.fq" 2>/dev/null | samtools view -c - 2>/dev/null)
    mp=$(bwa mem -t "$THREADS" -k "$K" -p "$REF" "$T/${S}_sc1.fq" 2>/dev/null | samtools view -c -F4 - 2>/dev/null)
  else
    tot=$(bwa mem -t "$THREADS" -k "$K" "$REF" "$T/${S}_sc1.fq" "$T/${S}_sc2.fq" 2>/dev/null | samtools view -c - 2>/dev/null)
    mp=$(bwa mem -t "$THREADS" -k "$K" "$REF" "$T/${S}_sc1.fq" "$T/${S}_sc2.fq" 2>/dev/null | samtools view -c -F4 - 2>/dev/null)
  fi
  rm -f "$T/${S}_sc1.fq" "$T/${S}_sc2.fq"
  local rate
  rate=$(awk -v a="$mp" -v b="$tot" 'BEGIN{ if(b>0) printf "%.1f", a*100/b; else print "NA" }')
  printf "%s\t%s\t%s\t%s\t%s\n" "$S" "$MOD" "$mp" "$tot" "$rate" >> "$OUT"
}

# 每个模块抽样（US 抽 8 个，其余各 3 个）
awk -F'\t' 'NR>1 && $3=="US"{print $1"\t"$3}' /mnt/c/SF_data/tools/cohort_formal_s2.tsv | shuf -n 8 --random-source=<(yes) > /tmp/.scr_us.tsv
for m in BR AF AM CN FL; do
  awk -F'\t' -v M="$m" 'NR>1 && $3==M{print $1"\t"$3}' /mnt/c/SF_data/tools/cohort_formal_s2.tsv | shuf -n 3 --random-source=<(yes) >> /tmp/.scr_us.tsv
done

while IFS=$'\t' read -r s mod; do
  screen_one "$s" "$mod"
done < /tmp/.scr_us.tsv
rm -f /tmp/.scr_us.tsv

echo "--- 抽样比对率（升序）---"
tail -n +2 "$OUT" | sort -t$'\t' -k5 -n | awk -F'\t' '{printf "  %-14s %-3s %s%%\n",$1,$2,$5}'
