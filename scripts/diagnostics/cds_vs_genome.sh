#!/usr/bin/env bash
# cds_vs_genome.sh —— 关键判别：CDS（保守编码区）vs 全基因组的 read 错配率
#   若 CDS 区 NM 显著低于全基因组  -> 全基因组的"高 NM"主要来自重复序列 mismatchapping
#   若 CDS 区 NM 与全基因组相当    -> 真实的、全基因组均匀的序列分化
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
GFF=/mnt/c/SF_data/00_ref/GCF_023101765.2_genomic.gff.gz
BAM=${1:-/home/hugo/data/03_align/SRR11528382.dedup.bam}
T=/home/hugo/data/tmp/cds
mkdir -p "$T"

echo "[1] 从 GFF 提取 CDS 区间（仅染色体级）"
gzip -dc "$GFF" | awk -F'\t' '$3=="CDS" && $1 ~ /^NC_/ {print $1"\t"($4-1)"\t"$5}' > "$T/cds.bed"
echo "    CDS 条数 = $(wc -l < "$T/cds.bed")"
awk '{s+=$3-$2}END{printf "    CDS 总长 = %d bp (%.1f%% of 383.9 Mb)\n", s, 100*s/383923118}' "$T/cds.bed"

echo
echo "[2] 用 GFF 的 gene 区间做对照（基因内所有区域）"
gzip -dc "$GFF" | awk -F'\t' '$3=="gene" && $1 ~ /^NC_/ {print $1"\t"($4-1)"\t"$5}' > "$T/gene.bed"
awk '{s+=$3-$2}END{printf "    gene 总长 = %d bp (%.1f%%)\n", s, 100*s/383923118}' "$T/gene.bed"

stat_nm() {
  local tag="$1"; shift
  echo "  --- $tag ---"
  samtools view "$@" 2>/dev/null | head -200000 | awk '
    { nm=-1; for(i=12;i<=NF;i++){ if($i ~ /^NM:i:/) nm=substr($i,6)+0 }
      mq=$5+0; n++; s+=nm; if(nm==0) z++; if(mq<20) lo++ }
    END{ printf "    reads=%d  平均NM=%.3f   NM==0: %.1f%%   MAPQ<20: %.1f%%\n", n, s/n, 100*z/n, 100*lo/n }'
}

echo
echo "[3] 三类区域对比（同一样本 $BAM，各采样 20 万条）"
stat_nm "CDS 区（编码序列，最保守）"   -L "$T/cds.bed"  -F 0x904 -q 1 "$BAM"
stat_nm "gene 区（含内含子/UTR）"     -L "$T/gene.bed" -F 0x904 -q 1 "$BAM"
stat_nm "全基因组（含大量重复序列）"  -F 0x904 -q 1 "$BAM"
