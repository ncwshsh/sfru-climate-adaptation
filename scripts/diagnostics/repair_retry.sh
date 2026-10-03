#!/usr/bin/env bash
cd /c/SF_data/01_raw
for f in SRR18441067_2.fastq.gz.partial29 SRR9289279_1.fastq.gz.partial13 SRR9289276_2.fastq.gz.partial13 SRR9289295_2.fastq.gz.partial18 SRR9656270_1.fastq.gz.partial21; do
  echo "/c/SF_data/01_raw/$f"
done | xargs -P 2 -I{} bash /c/SF_data/tools/repair_one.sh {}
echo "=== 重修批次结束 ==="
