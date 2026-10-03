#!/usr/bin/env bash
# 对比 BAM 的比对质量画像：MAPQ 分布、NM 错配数、softclip
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
A=/home/hugo/data/03_align
BAM=${1:-$A/SRR10980085.dedup.bam}
BAM2=${2:-$A/SRR11528382.dedup.bam}
N=${3:-2000000}
for b in "$BAM" "$BAM2"; do
  echo "=== $(basename "$b") ==="
  samtools view -@ 4 "$b" 2>/dev/null | head -"$N" | awk '
  {
    flag=$2+0; mapq=$5+0; cig=$6; nm=-1
    for(i=12;i<=NF;i++){ if($i ~ /^NM:i:/){ split($i,a,":"); nm=a[3]+0 } }
    n++
    if(int(flag/4)%2==1){ unm++; next }
    if(mapq>=60) mq3++; else if(mapq>=30) mq2++; else if(mapq>=10) mq1++; else mq0++
    if(nm>=0){ nm_sum+=nm; if(nm==0) nm0++; if(nm>5) nm5++; tot_nm++ }
    if(cig ~ /S/) sc++
    if(cig ~ /^[0-9]+M$/) perfect++
  }
  END{
    printf "  抽样=%d  unmapped=%d\n", n, unm+0
    printf "  MAPQ>=60: %.1f%%  30-59: %.1f%%  10-29: %.1f%%   <10: %.1f%%\n", 100*mq3/n, 100*mq2/n, 100*mq1/n, 100*mq0/n
    printf "  平均NM=%.2f   NM=0: %.1f%%   NM>5: %.1f%%  (n=%d)\n", nm_sum/tot_nm, 100*nm0/tot_nm, 100*nm5/tot_nm, tot_nm
    printf "  含softclip: %.1f%%   纯M cigar: %.1f%%\n", 100*sc/n, 100*perfect/n
  }'
  echo
done
