#!/usr/bin/env bash
# peek_fq.sh —— 直接看原始 FASTQ 的 reads 组成（不经过 BAM），判技术假象 vs 物种问题
# 用法（WSL 内）: bash /mnt/c/SF_data/tools/peek_fq.sh <R1路径>
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
F="$1"
echo "=== $F ==="
gzip -dc "$F" 2>/dev/null | head -40000 | awk 'NR%4==2' | \
awk '{
  s=$0; n=length(s)
  c=0; for(i=1;i<=n;i++){ch=substr(s,i,1); if(ch=="G") c++}
  sum+=c/n
  if (s ~ /G{20,}/) pg++
  tot++
  if (tot<=8) print "  "substr(s,1,70)
}
END{ printf "  reads=%d  平均G含量=%.1f%%  polyG20比例=%.1f%%\n", tot, sum*100/tot, pg*100/tot }'
