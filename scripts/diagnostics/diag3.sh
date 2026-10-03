#!/usr/bin/env bash
# diag3.sh —— 按 MAPQ 分档统计 NM + 插入片段分布 + 跨染色体配对比例
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
B=${1:-/home/hugo/data/03_align/SRR11528382.dedup.bam}

echo "===== $(basename "$B") ====="
samtools view -s 77.02 -F 0x904 -q 1 "$B" 2>/dev/null | head -300000 | awk '
{
  nm=-1; for(i=12;i<=NF;i++){ if($i ~ /^NM:i:/) nm=substr($i,6)+0 }
  mq=$5+0; rn=$3; mn=""; for(i=12;i<=NF;i++){ if($i ~ /^RN:i:/) 0 }
  tlen=$9+0; if(tlen<0) tlen=-tlen

  if(mq>=40){ n40++; s40+=nm; if(nm==0) z40++; if(nm>4) h40++ }
  else if(mq>=20){ n20++; s20+=nm; if(nm==0) z20++ }
  else { nlo++; slo+=nm; if(nm==0) zlo++ }

  tl[tlen]++
  all_nm += nm; n++
}
END{
  printf "总 reads = %d\n\n", n
  printf "MAPQ>=40 : %7d 条 (%.1f%%)   平均NM=%.2f   NM==0 %.1f%%   NM>4 %.1f%%\n", n40, 100*n40/n, (n40?s40/n40:0), (n40?100*z40/n40:0), (n40?100*h40/n40:0)
  printf "MAPQ20-39: %7d 条 (%.1f%%)   平均NM=%.2f   NM==0 %.1f%%\n", n20, 100*n20/n, (n20?s20/n20:0), (n20?100*z20/n20:0)
  printf "MAPQ<20  : %7d 条 (%.1f%%)   平均NM=%.2f   NM==0 %.1f%%\n", nlo, 100*nlo/n, (nlo?slo/nlo:0), (nlo?100*zlo/nlo:0)
  printf "\n全体平均 NM = %.2f\n", all_nm/n
}'

echo
echo "--- 插入片段 TLEN 分布 ---"
samtools view -s 77.02 -F 0x904 -f 0x2 "$B" 2>/dev/null | head -200000 | awk '
{ t=$9+0; if(t<0) t=-t; if(t>0) a[++k]=t }
END{ n=asort(a); if(n==0){print "  无"; exit}
  printf "  n=%d  p10=%d  p25=%d  中位=%d  p75=%d  p90=%d  max=%d\n", n, a[int(n*0.1)], a[int(n*0.25)], a[int(n*0.5)], a[int(n*0.75)], a[int(n*0.9)], a[n]
  big=0; for(i=1;i<=n;i++) if(a[i]>2000) big++
  printf "  TLEN>2000 占比 = %.1f%%\n", 100*big/n }' 2>/dev/null \
  || echo "  (gawk asort 不可用，改用 sort)"

echo
echo "--- 跨染色体配对 ---"
samtools view -s 77.02 -F 0x904 -f 0x2 "$B" 2>/dev/null | head -200000 | awk '
{ if($7!="=" && $7!="*") diff++; n++ }
END{ printf "  mate 在别的染色体: %d / %d = %.1f%%\n", diff, n, 100*diff/n }'
