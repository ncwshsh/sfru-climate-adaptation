#!/usr/bin/env bash
# inv.sh —— WSL 侧数据家底盘点
for d in /home/hugo/data/01_raw /home/hugo/data/03_align /home/hugo/data/04_variant /home/hugo/data/ref /home/hugo/data/tmp; do
  echo "===== $d ====="
  if [ -d "$d" ]; then
    ls -la "$d" 2>/dev/null | head -25
    echo "  [文件数] $(ls -1 "$d" 2>/dev/null | wc -l)"
  else
    echo "  (不存在)"
  fi
done
echo "===== BAM 清单（含索引）====="
find /home/hugo/data -maxdepth 2 -name "*.bam" -o -maxdepth 2 -name "*.bai" 2>/dev/null | sort
echo "===== VCF 清单 ====="
find /home/hugo/data -maxdepth 3 -name "*.vcf*" 2>/dev/null | sort
echo "===== 磁盘 ====="
df -h /home/hugo/data | tail -2
echo "===== 参考基因组 ====="
ls -la /home/hugo/data/ref 2>/dev/null
