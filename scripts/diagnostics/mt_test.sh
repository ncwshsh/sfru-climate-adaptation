#!/usr/bin/env bash
# mt_test.sh —— 线粒体对照（单拷贝、无重复、高深度）
#   核参考差异 ~2.7% 但线粒体差异很小  -> 问题在核基因组参考
#   线粒体差异也很大                    -> 样本归属/数据本身有问题
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
T=/home/hugo/data/ref/mt
mkdir -p "$T"

echo "[1] 下载 S. frugiperda 线粒体参考 NC_027836.1"
if [ ! -s "$T/mt.fasta" ]; then
  curl -fsSL --max-time 180 \
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=NC_027836.1&rettype=fasta&retmode=text" \
    -o "$T/mt.fasta" || { echo "    下载失败"; exit 1; }
fi
head -1 "$T/mt.fasta"
echo "    长度 = $(grep -v '^>' "$T/mt.fasta" | tr -d '\n' | wc -c) bp"

minimap2 -x sr -d "$T/mt.mmi" "$T/mt.fasta" 2>/dev/null

echo "[2] 取样本 100 万对 reads"
RAW=/home/hugo/data/01_raw
[ -s /tmp/m1.fq ] || pigz -dc "${RAW}/SRR11528382_1.fastq.gz" 2>/dev/null | head -4000000 > /tmp/m1.fq
[ -s /tmp/m2.fq ] || pigz -dc "${RAW}/SRR11528382_2.fastq.gz" 2>/dev/null | head -4000000 > /tmp/m2.fq

score() {
  local ref="$1" tag="$2"
  echo "  --- $tag ---"
  minimap2 -ax sr -t 8 "$ref" /tmp/m1.fq /tmp/m2.fq 2>/dev/null \
    | samtools view -F 0x904 - 2>/dev/null | awk '
    { nm=-1; for(i=12;i<=NF;i++){ if($i ~ /^NM:i:/) nm=substr($i,6)+0 } mq=$5+0
      n++; s+=nm; if(nm==0) z++; if(mq<20) lo++ }
    END{ if(n==0){print "    无 reads 比对"; exit}
         printf "    reads=%d  平均NM=%.3f   差异率=%.3f%%   NM==0: %.1f%%   MAPQ<20: %.1f%%\n", n, s/n, 100*s/n/150, 100*z/n, 100*lo/n }'
}

echo "[3] 同一批 reads，两个参考的对照"
score "$T/mt.mmi"                                   "线粒体 NC_027836.1（单拷贝、无重复、15 kb）"
score "/home/hugo/data/ref/ref_GCF_023101765.2.fna" "核基因组 GCF_023101765.2（383.9 Mb）"
