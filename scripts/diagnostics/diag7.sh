#!/usr/bin/env bash
# diag7.sh —— 对照实验：用参考自己切出的模拟 reads 比对回参考
# 预期 NM 应≈0。若也高 -> 比对器/参考结构问题；若≈0 -> 样本与参考确有真实差异
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
R=/home/hugo/data/ref/ref_GCF_023101765.2.fna
T=/home/hugo/data/tmp/sim
mkdir -p "$T"

echo "生成模拟 reads（NC_064236.1 前 1 Mb，每 150 bp 取一条）..."
samtools faidx "$R" NC_064236.1:1-1000000 2>/dev/null | grep -v '^>' | tr -d '\n' > "$T/seq.txt"
ls -la "$T/seq.txt"

awk '{
  w=150; k=0
  for(i=1; i<=length($0)-w+1; i+=w*3) { print ">sim" k++; print substr($0,i,w) }
}' "$T/seq.txt" > "$T/sim.fa"
echo "模拟 reads 数: $(grep -c '^>' "$T/sim.fa")"
rm -f "$T/seq.txt"

echo
echo "=== minimap2 -ax sr 回比对 ==="
minimap2 -ax sr "$R" "$T/sim.fa" 2>/dev/null \
  | samtools view -F 0x904 - 2>/dev/null \
  | awk '{ nm=-1; for(i=12;i<=NF;i++){ if($i ~ /^NM:i:/) nm=substr($i,6)+0 } mq=$5+0
           n++; s+=nm; if(nm==0) z++; if(mq<20) lo++ }
         END{ printf "  reads=%d  平均NM=%.3f   NM==0: %.1f%%   MAPQ<20: %.1f%%\n", n, s/n, 100*z/n, 100*lo/n }'

echo
echo "=== bwa mem 回比对（对照）==="
bwa mem -t 8 "$R" "$T/sim.fa" 2>/dev/null \
  | samtools view -F 0x904 - 2>/dev/null \
  | awk '{ nm=-1; for(i=12;i<=NF;i++){ if($i ~ /^NM:i:/) nm=substr($i,6)+0 } mq=$5+0
           n++; s+=nm; if(nm==0) z++; if(mq<20) lo++ }
         END{ printf "  reads=%d  平均NM=%.3f   NM==0: %.1f%%   MAPQ<20: %.1f%%\n", n, s/n, 100*z/n, 100*lo/n }'

echo
echo "=== 实测样本作对比（同一区域同源 reads）==="
samtools view -F 0x904 /home/hugo/data/03_align/SRR11528382.dedup.bam NC_064236.1:1-1000000 2>/dev/null | head -100000 | awk '
{ nm=-1; for(i=12;i<=NF;i++){ if($i ~ /^NM:i:/) nm=substr($i,6)+0 } mq=$5+0
  n++; s+=nm; if(nm==0) z++; if(mq<20) lo++ }
END{ printf "  实测 reads=%d  平均NM=%.3f   NM==0: %.1f%%   MAPQ<20: %.1f%%\n", n, s/n, 100*z/n, 100*lo/n }'
