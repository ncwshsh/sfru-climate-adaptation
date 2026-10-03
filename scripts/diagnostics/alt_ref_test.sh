#!/usr/bin/env bash
# alt_ref_test.sh —— 用第二个独立组装（GCA_012979215.2，中国农科院）做对照
# 若 NM 骤降 -> 参考特异问题；若仍高 -> 数据本身问题
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
ALT=/home/hugo/data/ref/alt
mkdir -p "$ALT"; cd "$ALT" || exit 1

BASE=https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/012/979/215/GCA_012979215.2_ASM1297921v2
F=GCA_012979215.2_ASM1297921v2_genomic.fna.gz

if [ ! -s "$F" ]; then
  echo "[1] 下载替代参考 $F ..."
  curl -fL --retry 5 --retry-delay 5 --max-time 2400 -o "$F" "$BASE/$F" || { echo "下载失败"; exit 1; }
fi
echo "    $(ls -la "$F")"
gzip -t "$F" && echo "    gzip OK" || { echo "    gzip 损坏"; exit 1; }

[ -s GCA_012979215.2.fna ] || gzip -dc "$F" > GCA_012979215.2.fna
samtools faidx GCA_012979215.2.fna 2>/dev/null
echo "    序列数 = $(grep -c '^>' GCA_012979215.2.fna)"
awk '/^>/{next}{s+=length($0)}END{print "    总长 = "s" bp"}' GCA_012979215.2.fna

if [ ! -s GCA_012979215.2.fna.mmi ]; then
  echo "[2] 建 minimap2 索引..."
  minimap2 -x sr -d GCA_012979215.2.fna.mmi GCA_012979215.2.fna 2>/dev/null
fi

echo "[3] 抽取 SRR11528382 前 100 万对 reads..."
RAW=/home/hugo/data/01_raw
pigz -dc "${RAW}/SRR11528382_1.fastq.gz" 2>/dev/null | head -4000000 > /tmp/sub1.fq
pigz -dc "${RAW}/SRR11528382_2.fastq.gz" 2>/dev/null | head -4000000 > /tmp/sub2.fq
echo "    R1=$(($(wc -l < /tmp/sub1.fq)/4)) 条  R2=$(($(wc -l < /tmp/sub2.fq)/4)) 条"

score() {
  local ref="$1" tag="$2"
  echo "  --- $tag ---"
  minimap2 -ax sr -t 8 "$ref" /tmp/sub1.fq /tmp/sub2.fq 2>/dev/null \
    | samtools view -F 0x904 - 2>/dev/null | awk '
    { nm=-1; for(i=12;i<=NF;i++){ if($i ~ /^NM:i:/) nm=substr($i,6)+0 } mq=$5+0
      n++; s+=nm; if(nm==0) z++; if(nm<=2) z2++; if(mq<20) lo++ }
    END{ printf "    reads=%d  平均NM=%.3f   NM==0: %.1f%%   NM<=2: %.1f%%   MAPQ<20: %.1f%%\n", n, s/n, 100*z/n, 100*z2/n, 100*lo/n }'
}

echo "[4] 两套参考对同一批 reads 的比对质量对比"
score "$ALT/GCA_012979215.2.fna" "替代参考 GCA_012979215.2（中国农科院）"
score "/home/hugo/data/ref/ref_GCF_023101765.2.fna" "当前参考 GCF_023101765.2（CSIRO）"
