#!/usr/bin/env bash
# 精确统计指定 FASTQ 的 reads 数，与 ENA 声明对账
export PATH=/usr/bin:/bin:$PATH
D=/home/hugo/data/01_raw
printf "%-44s %12s %10s\n" FILE READS SIZE_GB
for f in \
  "$D/SRR31304341_1.fastq.gz" \
  "$D/SRR10980085_1.fastq.gz" \
  "$D/SRR11528382_1.fastq.gz" \
  "$D/SRR12044633_1.fastq.gz" \
  "$D/SRR12044649_1.fastq.gz.partial30" \
  "$D/SRR12044649_1.fastq.gz.partial60" ; do
  [ -s "$f" ] || { printf "%-44s %12s %10s\n" "$(basename "$f")" "MISSING" "-"; continue; }
  n=$(zcat "$f" 2>/dev/null | wc -l)
  r=$((n/4))
  sz=$(stat -c%s "$f")
  gb=$(awk -v s="$sz" 'BEGIN{printf "%.2f", s/1073741824}')
  printf "%-44s %12s %10s\n" "$(basename "$f")" "$r" "$gb"
done
