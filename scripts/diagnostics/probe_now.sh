#!/usr/bin/env bash
# probe_now.sh —— 一次性摸清：BAM 真实深度 + 参考染色体表 + 快速验证 mpileup 可用
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
DATA=/home/hugo/data
REF=$DATA/ref/ref_GCF_023101765.2.fna

echo "===== 1. 参考基因组 fai（前 12 条 + 总长）====="
head -12 "${REF}.fai"
awk '{s+=$2} END{printf "总长=%d bp (%.1f Mb) 条数=%d\n", s, s/1e6, NR}' "${REF}.fai"

echo
echo "===== 2. 5 个 BAM 的真实比对深度（idxstats 比对碱基 / 基因组长）====="
GEN=$(awk '{s+=$2} END{print s}' "${REF}.fai")
for b in $DATA/03_align/*.dedup.bam; do
  n=$(basename "$b" .dedup.bam)
  # idxstats: 第3列 = mapped reads; 用 samtools view -c 更准，但慢。这里用 mapq>=20 的 read 数
  reads=$(samtools view -c -q 20 "$b" 2>/dev/null)
  # 每条 read 平均长度用 2*150 估算不对；直接从 flagstat 拿不到。用 samtools stats 太慢。
  # 折中：idxstats 的 mapped reads × 平均读长（由采样得到）
  samp=$(samtools view "$b" 2>/dev/null | head -20000 | awk '{s+=length($10); n++} END{if(n>0) printf "%.1f", s/n; else print 0}')
  idxr=$(samtools idxstats "$b" 2>/dev/null | awk '{s+=$3} END{print s}')
  dep=$(awk -v r="$idxr" -v L="$samp" -v g="$GEN" 'BEGIN{ if(L>0) printf "%.2f", r*L/g; else print 0 }')
  printf "  %-20s mapped_reads=%-12s avg_readlen=%-6s => %sx\n" "$n" "$idxr" "$samp" "$dep"
done

echo
echo "===== 3. mpileup 快速验证（单样本，单染色体，看能不能出记录）====="
B1=$(ls $DATA/03_align/*.dedup.bam | head -1)
CHR=$(head -1 "${REF}.fai" | cut -f1)
echo "  样本=$(basename $B1)  染色体=$CHR"
bcftools mpileup -f "$REF" -a AD,DP -q 20 -Q 20 -d 500 -r "$CHR" -Ou "$B1" 2>/tmp/mp.err \
  | bcftools call -m -v -a GQ -Oz -o $DATA/tmp/probe1.vcf.gz 2>>/tmp/mp.err
echo "  rc=$?"
echo "  mpileup stderr:"; head -5 /tmp/mp.err
echo "  记录数=$(bcftools view -H $DATA/tmp/probe1.vcf.gz 2>/dev/null | wc -l)"
echo "  stats:"
bcftools stats -F "$REF" $DATA/tmp/probe1.vcf.gz 2>/dev/null | grep -E "number of SNPs|number of records|Ts/Tv"
