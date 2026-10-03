#!/usr/bin/env bash
# align_s2_one.sh —— S2 队列单样本比对（bwa-mem2/bwa → sort → markdup → index → flagstat）
#
# 与 run_chr_align.sh / align_bwa_one.sh 的关系：
#   - 参考取 run_chr_align 的 ref_chr（31 条核染色体，自检必须恰好 31 条、0 scaffold、0 线粒体）
#   - 比对器取 align_bwa_one 的 bwa mem（实测比对率 97.3% vs minimap2 89.4%）
#   - 输入选择统一走 lib_select_fq.sh 的 pick_fq（体积降序、排除 .partN、认 .nrec 凭证）
#
# ★ interleaved 支持（2026-09-19 新增）：
#   CN 10 个样本在 ENA 是「PAIRED 但只有一个 FASTQ」（header 1/2、2/2 交错），
#   传入 --interleaved 后走 bwa mem -p（且线程级 pair 保持），否则浪费一半插入信息。
#
# 用法:
#   bash align_s2_one.sh <SRR> [--interleaved]
# 例:
#   bash align_s2_one.sh SRR29141578
#   bash align_s2_one.sh SRR9656262 --interleaved
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

s="${1:?需要 SRR}"
INTER=0
[ "${2:-}" = "--interleaved" ] && INTER=1

REF=/home/hugo/data/ref/ref_chr.fna
RAW=/mnt/c/SF_data/01_raw
ALN=/mnt/c/SF_data/03_align
TMP=/home/hugo/data/tmp
THREADS=${THREADS:-8}
# ★ MINSEED（-k）：2026-09-20 定为 15。
#   实测：坏样本（巴西种群，与 CSIRO 参考分化大）bwa -k19 仅 21.2% → -k15 37.2%（+16pp）；
#   好样本 94.4% → 96.3%（仅 +1.9pp）。**全队列统一用 15**（不能对部分样本换参数，
#   否则方法学不一致会变成与地理重合的批次效应），配合 ANGSD 阶段 MAPQ≥30/BQ≥20 控假阳性。
MINSEED=${MINSEED:-15}
# ★ ALIGNER：2026-09-20 定为 bwa-mem2（AVX2 构建）。
#   实测（同子集、同 -k15、同线程，比 CPU 时间不受抢核影响）：
#     好样本 SRR34858432: bwa CPU 2019.9s -> bm2 890.0s（2.27×），比对率 99.05% == 99.05%
#     巴西分化样本 SRR9289279: bwa 995.8s -> bm2 545.6s（1.83×），比对率 70.39% == 70.39%
#     **两个样本 primary mapped 条数完全一致**（1980932 / 563091）⇒ 结果等价可换器
#     全队列统一换（不能一部分 bwa 一部分 bm2，否则又变成与地理共线的批次效应）
#   ⚠️ 必须用 avx2 那个二进制：avx512bw 变体在本机 WSL 下起不来（rc=1）
#   ⚠️ 内存比 bwa 大：-t6 峰值 RSS 5.41 GB vs bwa 3.01 GB ⇒ 并发别超过 2
# ★ SAMT / SMEM：后处理（collate/fixmate/sort/markdup）的线程与排序内存。
#   2026-09-20 实测：换上 bwa-mem2 后，比对阶段只占 73%，**后处理占 27%**，
#   而它一直是 -@ 2，成为新的串行瓶颈（单样本 13 min，期间 18 核闲着）。
#   默认提到 -@ 3 / -m 1500M；若内存吃紧（看 `free -g` 的 available）可降回 2/1G。
SAMT=${SAMT:-3}
SMEM=${SMEM:-1500M}
ALIGNER=${ALIGNER:-bm2}
BM2BIN=${BM2BIN:-/home/hugo/tools/bwa-mem2-2.2.1_x64-linux/bwa-mem2.avx2}
ALNCMD=bwa
[ "$ALIGNER" = "bm2" ] && ALNCMD="$BM2BIN"
TAG=${TAG:-k15}
OUTBAM="${ALN}/${s}.${TAG}.dedup.bam"
LOG="${ALN}/${s}_${TAG}_run.log"

# ---------------------------------------------------------------------------
# ★ 单样本互斥锁（2026-09-20 事故后新增）
#   事故复盘：09:49 的调度链上层被打死，两个样本变成孤儿继续跑；10:43 又起新链，
#   新链从队首重新扫到同一批样本，导致 **两条管线同时写同一个 OUTBAM**（还共用
#   同一份 ${TMP}/${s}.bam）。本次验证 `samtools view -c` 与 flagstat 完全一致、
#   文件侥幸未损坏，但这种事不能指望运气。
#   机制：mkdir 原子的目录锁 + 记 PID；PID 已死则判为陈旧锁并接管。
#   ⚠️ 锁放在 **WSL 原生 /tmp**，不放 /mnt/c：drvfs 上 mkdir 偶发假失败，
#      互斥形同虚设（实测出现过）。所有链都在同一个 Ubuntu-24.04 里，/tmp 够用。
# ---------------------------------------------------------------------------
LOCKDIR="/tmp/.aln_lock_${s}_${TAG}"
mkdir -p /tmp 2>/dev/null
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  _oldpid=$(cat "$LOCKDIR/pid" 2>/dev/null)
  if [ -n "$_oldpid" ] && kill -0 "$_oldpid" 2>/dev/null; then
    echo "[$s] BUSY 已有实例在跑（pid=$_oldpid），跳过以免重复写 BAM"; exit 0
  fi
  echo "[$s] 接管陈旧锁（原 pid=${_oldpid:-未知} 已不存在）"
  rm -rf "$LOCKDIR" 2>/dev/null
  mkdir "$LOCKDIR" 2>/dev/null || { echo "[$s] FAIL 无法建锁"; exit 1; }
fi
echo $$ > "$LOCKDIR/pid"
trap 'rm -rf "$LOCKDIR" 2>/dev/null' EXIT INT TERM

# ---- 选 FASTQ ----
_libdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FQLIB="${FQLIB:-${_libdir}/lib_select_fq.sh}"
[ -f "$FQLIB" ] || { echo "[$s] FAIL 缺 $FQLIB"; exit 1; }
. "$FQLIB"

if [ "$INTER" = "1" ]; then
  # CN interleaved：单文件，_1 即全部（ENA 无 _2）
  r1=$(pick_fq "${RAW}/${s}_1.fastq.gz")
  r2=""
  [ -n "$r1" ] || { echo "[$s] SKIP 缺 interleaved FASTQ"; exit 0; }
else
  r1=$(pick_fq "${RAW}/${s}_1.fastq.gz")
  r2=$(pick_fq "${RAW}/${s}_2.fastq.gz")
  if [ -z "$r1" ] || [ -z "$r2" ]; then echo "[$s] SKIP 缺 FASTQ"; exit 0; fi
fi

# ---- 幂等：BAM + 索引 + flagstat 都在就跳过 ----
if [ -s "$OUTBAM" ] && [ -s "${OUTBAM}.bai" ]; then
  echo "[$s] SKIP 已有 dedup.bam"; exit 0
fi

[ -s "${REF}.fai" ] || { echo "[$s] FAIL 缺 ref fai"; exit 1; }
mkdir -p "$TMP" "$ALN"
exec > >(tee -a "$LOG") 2>&1

# ---- 参考自检：必须恰好 31 条核染色体 ----
nseq=$(wc -l < "${REF}.fai")
nnw=$(grep -c '^NW_' "${REF}.fai" || true)
nmt=$(grep -c '^NC_027836' "${REF}.fai" || true)
echo "=== start $(date '+%F %T') | $s | interleaved=$INTER | 线程=$THREADS ==="
echo "  参考自检: 序列数=$nseq(应31) NW_=$nnw(应0) 线粒体=$nmt(应0)"
if [ "$nseq" != "31" ] || [ "$nnw" != "0" ] || [ "$nmt" != "0" ]; then
  echo "[$s] FATAL 参考不纯，拒绝继续"; exit 1
fi
echo "  输入: $(basename "$r1")${r2:+  |  $(basename "$r2")}"

# ---- 比对 + 后处理（一条管道到底） ----
# ★ 2026-09-20 管线精简：**去掉了 bwa 之后那一次坐标排序**。
#   旧管线 bwa | sort(坐标) → tmp.bam ；再 collate(按名) → fixmate → sort(坐标) → markdup，
#   第一遍全排序写完盘、紧接着 collate 又按名字重排一遍，纯属浪费
#   （collate 本来就是设计来直接吃 bwa 的 SAM 流的）。
#   实测（bench_pipe.sh，巴西样本 40 万对，同参数）：
#     A 双排序 real 231.2 s / CPU 587.5 s
#     B 单排序 real 175.4 s / CPU 582.3 s   ← 墙钟快 24%，CPU 几乎不变（省的是 I/O 等待）
#     **两者 flagstat 完全一致**：563091 primary mapped (70.39%)、4405 primary duplicates
#   ⇒ 结果等价、更快、峰值内存还更低（少一个排序进程）
echo "--- $ALIGNER mem -k $MINSEED → collate/fixmate/sort/markdup  $(date '+%T') ---"
if [ "$INTER" = "1" ]; then
  "$ALNCMD" mem -t "$THREADS" -M -k "$MINSEED" -p \
    -R "@RG\tID:${s}\tSM:${s}\tPL:BGISEQ\tLB:${s}\tPU:unit1" \
    "$REF" "$r1" 2>/dev/null \
    | samtools collate -@ "$SAMT" -T "${TMP}/${s}_c" -o - - \
    | samtools fixmate -@ "$SAMT" -m - - \
    | samtools sort -@ "$SAMT" -m "$SMEM" -T "${TMP}/${s}_md" -o - - \
    | samtools markdup -@ "$SAMT" - "$OUTBAM"
else
  "$ALNCMD" mem -t "$THREADS" -M -k "$MINSEED" \
    -R "@RG\tID:${s}\tSM:${s}\tPL:ILLUMINA\tLB:${s}\tPU:unit1" \
    "$REF" "$r1" "$r2" 2>/dev/null \
    | samtools collate -@ "$SAMT" -T "${TMP}/${s}_c" -o - - \
    | samtools fixmate -@ "$SAMT" -m - - \
    | samtools sort -@ "$SAMT" -m "$SMEM" -T "${TMP}/${s}_md" -o - - \
    | samtools markdup -@ "$SAMT" - "$OUTBAM"
fi
PS=("${PIPESTATUS[@]}")
# 管道成员：0=比对器 1=collate 2=fixmate 3=sort 4=markdup
if [ "${PS[0]:-0}" -ne 0 ] || [ "${PS[4]:-0}" -ne 0 ]; then
  echo "[$s] FAIL 管道（比对器=${PS[0]:-?} markdup=${PS[4]:-?}）"; rm -f "$OUTBAM"; exit 1
fi

samtools index -@ ${SAMT:-3} "$OUTBAM"
samtools flagstat -@ ${SAMT:-3} "$OUTBAM" > "${ALN}/${s}.${TAG}.flagstat"
rm -f "${TMP}/${s}.bam"

echo "=== 结果 $(date '+%F %T') ==="
grep -E 'in total|primary mapped \(|primary duplicates' "${ALN}/${s}.${TAG}.flagstat"
echo "--- 染色体 raw 深度 ---"
samtools idxstats "$OUTBAM" | awk '$2>1000000{m+=$3; l+=$2; n++} END{printf "  raw 深度 = %.2f x（%d 条 / %d bp）\n", m*151/l, n, l}'
echo "=== end ==="
