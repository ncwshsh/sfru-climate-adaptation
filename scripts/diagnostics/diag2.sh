#!/usr/bin/env bash
# diag2.sh —— 全基因组随机采样诊断 + bwa/minimap2 对照
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

scan() {
  local B="$1"; local tag="$2"
  if [ ! -s "$B" ]; then echo "  [缺] $B"; return; fi
  echo "===== $tag : $(basename "$B") ====="
  samtools view -s 42.01 -F 0x904 "$B" 2>/dev/null | head -200000 | awk '
  { nm=-1; for(i=12;i<=NF;i++){ if($i ~ /^NM:i:/) nm=substr($i,6)+0 }
    mq=$5+0; n++; s_nm+=nm; s_mq+=mq; s_len+=length($10)
    if(nm==0) nm0++; if(nm<=2) nm2++; if(nm>4) hi++; if(mq<20) lo++; if(mq<10) lo10++
  }
  END{ if(n==0){print "  无 reads"; exit}
    printf "  reads=%d  平均长度=%.0fbp\n", n, s_len/n
    printf "  平均 NM=%.2f    NM==0: %.1f%%   NM<=2: %.1f%%   NM>4: %.1f%%\n", s_nm/n, 100*nm0/n, 100*nm2/n, 100*hi/n
    printf "  平均 MAPQ=%.1f   MAPQ<20: %.1f%%   MAPQ<10: %.1f%%\n", s_mq/n, 100*lo/n, 100*lo10/n }'
  echo
}

scan /mnt/c/SF_data/03_align/SRR31304341.dedup.bam "对照A · bwa 比对 · 山西"
scan /home/hugo/data/03_align/SRR10980085.dedup.bam  "实验B · minimap2 · 波多黎各"
scan /home/hugo/data/03_align/SRR11528382.dedup.bam  "实验C · minimap2 · 浙江"
