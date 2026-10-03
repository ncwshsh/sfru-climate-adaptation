#!/usr/bin/env bash
# bench_bwamem2.sh —— bwa  vs  bwa-mem2(avx2)  单样本基准
#
# 为什么做：全队列 -k15 重比对实测整机吞吐只有 3.99 GB/h（k19 是 6.36 GB/h），
# 剩余 265 GB 要 66 小时。bwa-mem2 是 bwa 的 SIMD 重写版，宣称 1.3~3 倍加速，
# 值得先花一小时验证，再决定要不要全队列换器。
#
# 设计要点：
#   1. **同一子集、同一 -k、同一线程数**，两边只差比对器
#   2. 生产链还在跑（占 16 线程），所以**比 CPU 时间（user+sys）而不是墙钟**——
#      CPU 时间不受"抢到几个核"影响，才是公平的算法效率比较
#   3. 取两个样本：GOOD（已完成，全量 bwa-k15 结果已知）+ BAD（巴西分化种群，
#      这才是 -k15 真正要救的样本，必须确认新比对器在它身上也不退化）
#   4. 比对率口径：primary mapped = -F 2308；primary 总数 = -F 2304
#      （别用 -F4，那会把 secondary/supplementary 混进来，历史上虚高到 105%）
#
# 用法（在 WSL 内）:
#   bash /mnt/c/SF_data/tools/bench_bwamem2.sh
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

REF=/home/hugo/data/ref/ref_chr.fna
BM2DIR=/home/hugo/tools/bwa-mem2-2.2.1_x64-linux
BM2=$BM2DIR/bwa-mem2.avx2          # ⚠ 必须用 avx2：avx512bw 变体在 WSL 下起不来（rc=1）
TMP=/home/hugo/data/tmp/bench
RAW=/mnt/c/SF_data/01_raw
LOG=/mnt/c/SF_data/tools/bench_bwamem2.log
NREC=${NREC:-1000000}   # 每个文件取多少条记录（=多少对）
THR=${THR:-4}
K=${K:-15}

mkdir -p "$TMP"
exec > >(tee -a "$LOG") 2>&1
echo "===== $(date '+%F %T') 基准开始  记录数=$NREC/端  线程=$THR  -k=$K ====="
echo "  CPU: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"

# ---------- 1. 索引 ----------
echo "--- $(date '+%T') bwa-mem2 index ---"
if [ -s "${REF}.0123" ]; then
  echo "  索引已存在，跳过"
else
  "$BM2" index "$REF"
fi
ls -la "${REF}".0* 2>/dev/null | head -6

# ---------- 2. 取子集 ----------
sub() {
  local srr=$1 idx=$2 out=$3 f
  f=$(ls -S "${RAW}/${srr}_${idx}.fastq.gz"* 2>/dev/null | grep -vE '\.part[0-9]+$' | grep -v '\.nrec\.' | head -1)
  [ -n "$f" ] || { echo "  [FAIL] 缺 ${srr}_${idx}"; return 1; }
  echo "  子集: $(basename "$f") -> $(basename "$out")"
  zcat "$f" | head -n $((NREC * 4)) > "$out"
}

# ---------- 3. 跑基准 ----------
run_bench() {
  local srr=$1 tag=$2 ref_rate=$3
  local r1="$TMP/${srr}_R1.fastq" r2="$TMP/${srr}_R2.fastq"
  if [ ! -s "$r1" ] || [ ! -s "$r2" ]; then
    sub "$srr" 1 "$r1" && sub "$srr" 2 "$r2" || return 1
  fi
  echo
  echo "########## $tag  $srr  （已知比对率: $ref_rate） ##########"
  for aln in bwa bm2; do
    local out="$TMP/${srr}_${aln}.sam" tt="$TMP/${srr}_${aln}.time"
    echo "--- $(date '+%T') $aln ---"
    if [ "$aln" = bwa ]; then
      /usr/bin/time -f "real %e s | user %U s | sys %S s | cpu %P" -o "$tt" \
        bwa mem -t "$THR" -k "$K" "$REF" "$r1" "$r2" > "$out" 2>/dev/null
    else
      /usr/bin/time -f "real %e s | user %U s | sys %S s | cpu %P" -o "$tt" \
        "$BM2" mem -t "$THR" -k "$K" "$REF" "$r1" "$r2" > "$out" 2>/dev/null
    fi
    echo "  $(cat "$tt")"
    local mapped primary
    mapped=$(samtools view -c -F 2308 "$out")
    primary=$(samtools view -c -F 2304 "$out")
    printf "  primary mapped = %d / %d = %.2f%%\n" \
      "$mapped" "$primary" "$(awk -v a="$mapped" -v b="$primary" 'BEGIN{printf 100*a/b}')"
    printf "  %s\t%s\t%s\t%s\n" "$srr" "$aln" "$(cat "$tt" | tr -s ' ')" "$mapped/$primary" >> "$TMP/summary.tsv"
    rm -f "$out"
  done
}

: > "$TMP/summary.tsv"
run_bench SRR34858432 GOOD "99.04%（bwa -k15 全量）"
run_bench SRR9289279  BAD  "69.3%（bwa -k15 抽样 10 万条）"

echo
echo "===== $(date '+%F %T') 基准结束 ====="
echo "--- 汇总 ---"
cat "$TMP/summary.tsv"
