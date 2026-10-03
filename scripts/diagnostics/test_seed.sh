#!/usr/bin/env bash
# test_seed.sh —— 用抽样 reads 对比 bwa 默认 seed(-k19) 与宽松 seed(-k15)、minimap2 的比对率
# 目的：判断低比对率是「种群分化+seed 太严」还是「数据本身垃圾」
# 用法（WSL 内）: bash /mnt/c/SF_data/tools/test_seed.sh <SRR> <R1> <R2>
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
S="$1"; R1="$2"; R2="$3"
REF=/home/hugo/data/ref/ref_chr.fna
T=/home/hugo/data/tmp
mkdir -p "$T"
N=${N:-400000}     # 每条 mate 抽样行数（N 行 = N/4 条 reads）

gzip -dc "$R1" 2>/dev/null | head -"$N" > "$T/${S}_s1.fq"
gzip -dc "$R2" 2>/dev/null | head -"$N" > "$T/${S}_s2.fq"

for k in 19 15; do
  r=$(bwa mem -t 6 -k $k "$REF" "$T/${S}_s1.fq" "$T/${S}_s2.fq" 2>/dev/null \
      | samtools view -c -F4 - 2>/dev/null)
  tot=$(bwa mem -t 6 -k $k "$REF" "$T/${S}_s1.fq" "$T/${S}_s2.fq" 2>/dev/null \
      | samtools view -c - 2>/dev/null)
  echo "  $S  bwa -k$k : 比对上 $r / 总 $tot"
done

m=$(minimap2 -ax sr -t 6 "$REF" "$T/${S}_s1.fq" "$T/${S}_s2.fq" 2>/dev/null \
    | samtools view -c -F4 - 2>/dev/null)
mt=$(minimap2 -ax sr -t 6 "$REF" "$T/${S}_s1.fq" "$T/${S}_s2.fq" 2>/dev/null \
    | samtools view -c - 2>/dev/null)
echo "  $S  minimap2  : 比对上 $m / 总 $mt"

rm -f "$T/${S}_s1.fq" "$T/${S}_s2.fq"
