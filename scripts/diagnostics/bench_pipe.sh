#!/usr/bin/env bash
# bench_pipe.sh —— 验证「去掉第一次坐标排序」是否可行且更快
#
# 现行管线（每个样本）：
#   bwa-mem2 | sort(坐标) -> TMP.bam ; collate(按名) | fixmate | sort(坐标) | markdup -> OUT
#                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   这一步把 bwa 的输出先按坐标排一遍、写盘，紧接着 collate 又要按名字重排一遍。
#   collate 本来就可以直接吃 bwa 的 SAM 流（samtools 文档：collate 就是为替代
#   `sort -n` 给 fixmate 做准备的）⇒ 这一遍全排序是纯浪费。
#
# 候选管线：bwa-mem2 | collate | fixmate | sort | markdup -> OUT
#
# 验证口径：
#   1) 结果必须一致 —— 比 flagstat 的 primary mapped / duplicates
#   2) 比 CPU 时间（user+sys），不比墙钟（生产链在抢核）
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

REF=/home/hugo/data/ref/ref_chr.fna
BM2=/home/hugo/tools/bwa-mem2-2.2.1_x64-linux/bwa-mem2.avx2
T=/home/hugo/data/tmp/bench
s=${1:-SRR9289279}          # 默认用巴西分化样本（子集 40 万对，跑得快）
THR=${THR:-4}
SMEM=${SMEM:-1G}
SAMT=${SAMT:-2}
r1=$T/${s}_R1.fastq; r2=$T/${s}_R2.fastq
[ -s "$r1" ] && [ -s "$r2" ] || { echo "缺子集 $s（先跑 bench2.sh 生成）"; exit 1; }

echo "########## 管线对比  $s  线程=$THR SAMT=$SAMT SMEM=$SMEM ##########"

# ---- A：现行（双排序）----
echo "--- $(date '+%T') A 现行：bwa-mem2 | sort -> tmp ; collate|fixmate|sort|markdup ---"
/usr/bin/time -f "A: real %e user %U sys %S" -o $T/A.time bash -c "
$BM2 mem -t $THR -M -k 15 $REF $r1 $r2 2>/dev/null \
  | samtools sort -@ $SAMT -m $SMEM -T $T/A_s -o $T/A.bam -
samtools collate -@ $SAMT -T $T/A_c -o - $T/A.bam \
  | samtools fixmate -@ $SAMT -m - - \
  | samtools sort -@ $SAMT -m $SMEM -T $T/A_md -o - - \
  | samtools markdup -@ $SAMT - $T/A.out.bam
"
cat $T/A.time
samtools index -@ 2 $T/A.out.bam
echo "  A flagstat:"; grep -E "primary mapped|primary duplicates" <(samtools flagstat $T/A.out.bam) | sed 's/^/    /'

# ---- B：候选（单排序）----
echo "--- $(date '+%T') B 候选：bwa-mem2 | collate|fixmate|sort|markdup ---"
/usr/bin/time -f "B: real %e user %U sys %S" -o $T/B.time bash -c "
$BM2 mem -t $THR -M -k 15 $REF $r1 $r2 2>/dev/null \
  | samtools collate -@ $SAMT -T $T/B_c -o - - \
  | samtools fixmate -@ $SAMT -m - - \
  | samtools sort -@ $SAMT -m $SMEM -T $T/B_md -o - - \
  | samtools markdup -@ $SAMT - $T/B.out.bam
"
cat $T/B.time
samtools index -@ 2 $T/B.out.bam
echo "  B flagstat:"; grep -E "primary mapped|primary duplicates" <(samtools flagstat $T/B.out.bam) | sed 's/^/    /'

echo
echo "=== 结论看这里：两条 flagstat 必须一致，B 的 CPU 时间应明显更小 ==="
rm -f $T/A.bam $T/A_s* $T/A_c* $T/B_c* 2>/dev/null
