#!/usr/bin/env bash
# 从 FASTQ 层面测真实序列重复率（awk 内部哈希，不用 sort）
export PATH=/usr/bin:/bin:$PATH
D=/home/hugo/data/01_raw
N=600000
for f in "$D/SRR10980085_1.fastq.gz" "$D/SRR11528382_1.fastq.gz" "$D/SRR31304341_1.fastq.gz"; do
  [ -s "$f" ] || continue
  printf "%-30s " "$(basename "$f")"
  zcat "$f" 2>/dev/null | head -$((N*4)) | awk '
    NR%4==2 { n++; s[$0]++ }
    END{ d=length(s); printf "reads=%d  distinct=%d  重复read占比=%.2f%%\n", n, d, 100*(n-d)/n }' 2>/dev/null || echo "(失败)"
done
