#!/usr/bin/env bash
# alt_ref_test2.sh —— 替代参考对照（带大小校验的续传下载）
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
ALT=/home/hugo/data/ref/alt
mkdir -p "$ALT"; cd "$ALT" || exit 1
BASE=https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/012/979/215/GCA_012979215.2_ASM1297921v2
F=GCA_012979215.2_ASM1297921v2_genomic.fna.gz

EXP=$(curl -sIL --max-time 120 "$BASE/$F" | tr -d '\r' | awk 'tolower($1)=="content-length:"{v=$2} END{print v}')
echo "[1] 官方文件大小 = ${EXP:-未知}"

if [ -n "$EXP" ]; then
  for i in 1 2 3 4 5 6 7 8 9 10; do
    CUR=$(stat -c%s "$F" 2>/dev/null || echo 0)
    echo "    第 $i 轮：本地 $CUR / 官方 $EXP"
    [ "$CUR" = "$EXP" ] && { echo "    ✅ 大小一致，下载完成"; break; }
    curl -fL -C - --retry 8 --retry-delay 5 --retry-all-errors --max-time 1200 -o "$F" "$BASE/$F" >/dev/null 2>&1
    sleep 2
  done
fi
ls -la "$F"
gzip -t "$F" 2>/dev/null && echo "    ✅ gzip 校验通过" || { echo "    ❌ gzip 仍损坏，退出"; exit 1; }

[ -s GCA_012979215.2.fna ] || gzip -dc "$F" > GCA_012979215.2.fna
samtools faidx GCA_012979215.2.fna 2>/dev/null
echo "[2] 序列数 = $(grep -c '^>' GCA_012979215.2.fna)   总长 = $(awk '/^>/{next}{s+=length($0)}END{print s}' GCA_012979215.2.fna) bp"

if [ ! -s GCA_012979215.2.fna.mmi ]; then
  echo "[3] 建 minimap2 索引（约 2-3 分钟）..."
  minimap2 -x sr -d GCA_012979215.2.fna.mmi GCA_012979215.2.fna 2>/dev/null
fi
ls -la GCA_012979215.2.fna.mmi 2>/dev/null

echo "[4] 抽 100 万对 reads 做对照"
RAW=/home/hugo/data/01_raw
[ -s /tmp/sub1.fq ] || pigz -dc "${RAW}/SRR11528382_1.fastq.gz" 2>/dev/null | head -4000000 > /tmp/sub1.fq
[ -s /tmp/sub2.fq ] || pigz -dc "${RAW}/SRR11528382_2.fastq.gz" 2>/dev/null | head -4000000 > /tmp/sub2.fq
echo "    R1=$(($(wc -l < /tmp/sub1.fq)/4)) 对"

score() {
  local ref="$1" tag="$2"
  echo "  --- $tag ---"
  minimap2 -ax sr -t 8 "$ref" /tmp/sub1.fq /tmp/sub2.fq 2>/dev/null \
    | samtools view -F 0x904 - 2>/dev/null | awk '
    { nm=-1; for(i=12;i<=NF;i++){ if($i ~ /^NM:i:/) nm=substr($i,6)+0 } mq=$5+0
      n++; s+=nm; if(nm==0) z++; if(nm<=2) z2++; if(mq<20) lo++ }
    END{ printf "    reads=%d  平均NM=%.3f   NM==0: %.1f%%   NM<=2: %.1f%%   MAPQ<20: %.1f%%\n", n, s/n, 100*z/n, 100*z2/n, 100*lo/n }'
}

echo "[5] 两套参考对比（同一样本 SRR11528382）
    =========================================="
score "$ALT/GCA_012979215.2.fna" "替代参考 GCA_012979215.2（中国农科院，染色体级）"
score "/home/hugo/data/ref/ref_GCF_023101765.2.fna" "当前参考 GCF_023101765.2（CSIRO RefSeq）"
