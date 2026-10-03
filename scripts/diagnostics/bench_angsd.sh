#!/usr/bin/env bash
# bench_angsd.sh —— 找出 ANGSD 在本机为什么慢，并给出最快的可接受配置
#
# 背景：首轮全基因组试跑外推要 60~80 小时，不可接受。
# 嫌疑最大的是 **-baq 1（-C 50）**：BAQ 要对每条 read 重算碱基比对质量，
# 214 个样本 × 全基因组，代价极高；而本队列是低深度（~6x）+ ANGSD 似然框架，
# BAQ 的收益本来就小（它主要是为"硬叫基因型"设计的）。
#
# 做法：在同一段 500 kb 区间上跑几种配置，比墙钟（都是单任务独占，可比）。
set -uo pipefail
export PATH=/home/hugo/mamba/envs/gea/bin:$PATH

REF=/home/hugo/data/ref/ref_chr.fna
BAMLIST=/mnt/c/SF_data/tools/bamlist_keep214.txt
REG=${REG:-NC_064236.1:10000000-10500000}
THR=${THR:-20}
OUTD=/home/hugo/data/angsd/bench
mkdir -p "$OUTD"

run() {
  local name=$1; shift
  local t0=$(date +%s)
  angsd -b "$BAMLIST" -ref "$REF" \
    -uniqueOnly 1 -remove_bads 1 -only_proper_pairs 1 -trim 0 \
    -minMapQ 30 -minQ 20 -minInd 171 -setMinDepthInd 1 \
    -GL 1 -doGlf 2 -doMajorMinor 1 -doMaf 1 -SNP_pval 1e-6 -minMaf 0.05 \
    -P "$THR" -r "$REG" -out "$OUTD/$name" "$@" > "$OUTD/$name.log" 2>&1
  local rc=$?
  local t1=$(date +%s)
  local nsnp=$(( $(zcat "$OUTD/$name.beagle.gz" 2>/dev/null | wc -l) - 1 ))
  printf "  %-14s 用时 %4ds  位点 %6d  rc=%d  %s\n" \
    "$name" $((t1-t0)) "$nsnp" "$rc" "$*"
}

echo "===== ANGSD 配置基准  区间 $REG  线程 $THR  $(date '+%F %T') ====="
run "A_baq1_C50"  -baq 1 -C 50
run "B_baq0"      -baq 0
run "C_baq1_noC"  -baq 1
echo "===== 基准结束 $(date '+%T') ====="
echo
echo "判读：若 B 明显快于 A 且位点数差别不大 ⇒ 全基因组用 -baq 0（低深度 + 似然框架下可接受）"
