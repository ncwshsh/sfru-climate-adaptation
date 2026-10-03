#!/usr/bin/env bash
# diag4.sh —— 错配是均匀分布(真实分化)还是局部聚集(组装/重复问题)？
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
B=${1:-/home/hugo/data/03_align/SRR11528382.dedup.bam}
REF=/home/hugo/data/ref/ref_GCF_023101765.2.fna

echo "=========== [1] 参考基因组基本特征 ==========="
awk '
  /^>/ { if(name!="") printf "  %-16s %14d bp  N=%d (%.2f%%)\n", name, len, ncnt, 100*ncnt/len
         name=substr($1,2); len=0; ncnt=0; next }
  { len+=length($0); t=$0; ncnt+=gsub(/[Nn]/,"",t) }
  END { if(name!="") printf "  %-16s %14d bp  N=%d (%.2f%%)\n", name, len, ncnt, 100*ncnt/len }
' "$REF" | head -40

echo
echo "=========== [2] 按 1 Mb 分箱的平均 NM（采样 30 万条 MAPQ>=20 的 reads）==========="
samtools view -s 77.03 -F 0x904 -q 20 "$B" 2>/dev/null | head -300000 | awk '
{
  nm=-1; for(i=12;i<=NF;i++){ if($i ~ /^NM:i:/) nm=substr($i,6)+0 }
  key = $3 "_" int($4/1000000)
  s[key]+=nm; c[key]++
  all+=nm; n++
  if(nm==0) z++
}
END{
  printf "  全体: reads=%d  平均NM=%.2f  NM==0=%.1f%%\n\n", n, all/n, 100*z/n
  for(k in s) printf "%s\t%.2f\t%d\n", k, s[k]/c[k], c[k]
}' | sort -k2,2gr > /tmp/bins.txt

echo "  --- 错配最高的 15 个 1Mb 箱 ---"
head -15 /tmp/bins.txt | awk -F'\t' '{printf "    %-22s 平均NM=%.2f  reads=%d\n", $1, $2, $3}'
echo "  --- 错配最低的 15 个 1Mb 箱 ---"
tail -15 /tmp/bins.txt | awk -F'\t' '{printf "    %-22s 平均NM=%.2f  reads=%d\n", $1, $2, $3}'

echo
echo "  --- 全基因组平均 NM 的分布直方图（每 0.5 一档）---"
awk -F'\t' '{b=int($2/0.5)*0.5; h[b]++} END{for(k in h) printf "%.1f\t%d\n", k, h[k]}' /tmp/bins.txt \
  | sort -g | awk '{printf "    NM %4.1f : %s\n", $1, substr("################################################################", 1, $2)}'
