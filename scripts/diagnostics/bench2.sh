#!/usr/bin/env bash
# bench2.sh —— 单样本 bwa vs bwa-mem2 基准（前台跑；索引已建好，不重建）
#
# 用法: bash /mnt/c/SF_data/tools/bench2.sh <SRR> <标签> [线程数] [每端记录数]
# 例  : bash bench2.sh SRR34858432 GOOD 4 1000000
#
# 关键：**比 CPU 时间（user+sys），不是墙钟**——生产链还占着 16 线程，
#       墙钟取决于抢到几个核，CPU 时间才是算法效率本身。
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

s=${1:?需要 SRR}
tag=${2:-}
THR=${3:-4}
NREC=${4:-1000000}
REF=/home/hugo/data/ref/ref_chr.fna
BM2=/home/hugo/tools/bwa-mem2-2.2.1_x64-linux/bwa-mem2.avx2
TMP=/home/hugo/data/tmp/bench
RAW=/mnt/c/SF_data/01_raw
SUM=$TMP/summary.tsv
mkdir -p "$TMP"
[ -f "$SUM" ] || printf "SRR\ttag\taligner\treal_s\tuser_s\tsys_s\tmapped\tprimary\trate_pct\n" > "$SUM"

sub() {
  local idx=$1 out=$2 f
  f=$(ls -S "${RAW}/${s}_${idx}.fastq.gz"* 2>/dev/null | grep -vE '\.part[0-9]+$' | grep -v '\.nrec\.' | head -1)
  [ -n "$f" ] || { echo "  [FAIL] 缺 ${s}_${idx}"; return 1; }
  echo "  子集 $(basename "$f") -> $(basename "$out")"
  zcat "$f" | head -n $((NREC * 4)) > "$out"
  echo "    $(wc -l < "$out") 行"
}

r1=$TMP/${s}_R1.fastq; r2=$TMP/${s}_R2.fastq
[ -s "$r1" ] || sub 1 "$r1"
[ -s "$r2" ] || sub 2 "$r2"
[ -s "$r1" ] && [ -s "$r2" ] || { echo "子集不齐，退出"; exit 1; }

ONLY=${5:-both}
[ "$ONLY" = both ] && ONLY="bwa bm2"
echo "########## $tag  $s  记录 $((NREC)) 对  线程 $THR  -k 15  只跑: $ONLY ##########"
for aln in $ONLY; do
  out=$TMP/${s}_${aln}.sam; tt=$TMP/${s}_${aln}.time
  echo "--- $(date '+%T') $aln ---"
  if [ "$aln" = bwa ]; then
    /usr/bin/time -f "%e %U %S" -o "$tt" bwa mem -t "$THR" -k 15 "$REF" "$r1" "$r2" > "$out" 2>/dev/null
  else
    /usr/bin/time -f "%e %U %S" -o "$tt" "$BM2" mem -t "$THR" -k 15 "$REF" "$r1" "$r2" > "$out" 2>/dev/null
  fi
  read -r rl us sy < "$tt"
  mapped=$(samtools view -c -F 2308 "$out")
  primary=$(samtools view -c -F 2304 "$out")
  rate=$(awk -v a="$mapped" -v b="$primary" 'BEGIN{printf "%.2f", 100*a/b}')
  printf "  %-4s real=%6.1fs  user=%6.1fs  sys=%5.1fs  CPU=%7.1fs  mapped=%d/%d = %s%%\n" \
    "$aln" "$rl" "$us" "$sy" "$(awk -v a=$us -v b=$sy 'BEGIN{print a+b}')" "$mapped" "$primary" "$rate"
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$s" "$tag" "$aln" "$rl" "$us" "$sy" "$mapped" "$primary" "$rate" >> "$SUM"
  rm -f "$out"
done
echo "--- 汇总 ---"
tail -3 "$SUM"
