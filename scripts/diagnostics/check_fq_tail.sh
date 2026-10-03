#!/usr/bin/env bash
# 诊断 partial60 的 FASTQ 结构：末尾记录是否完整、记录总数
export PATH=/usr/bin:/bin:$PATH
D=/home/hugo/data/01_raw
for f in "$D/SRR12044649_1.fastq.gz.partial60" "$D/SRR12044649_2.fastq.gz.partial60" \
         "$D/SRR12044649_1.fastq.gz.partial30" "$D/SRR12044649_2.fastq.gz.partial30"; do
  [ -s "$f" ] || continue
  echo "=================================================="
  echo "文件: $(basename "$f")   $(stat -c%s "$f") B"
  echo "--- 末尾 8 行（4行一条记录，看条数是否整）---"
  zcat "$f" 2>/dev/null | tail -8 | awk '{ printf "  行%-2d len=%-4d  %s\n", NR, length($0), substr($0,1,60) }'
  echo "--- 总行数 / 记录数 / 是否有半条 ---"
  zcat "$f" 2>/dev/null | awk '
    { n++; if(NR%4==1) l1=$0; else if(NR%4==2) l2=length($0); else if(NR%4==0){ if(length($0)!=l2) bad++ } }
    END{ printf "  总行数=%d  完整4行块=%d  余数=%d  SEQ/QUAL长度不符的记录=%d\n", n, int(n/4), n%4, bad+0 }'
done
