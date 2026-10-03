#!/usr/bin/env bash
# fix_index.sh —— 检查所有 dedup.bam 的索引，缺的补建
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
cd /home/hugo/data/03_align || exit 1

echo "=== 索引检查 ==="
for f in *.dedup.bam; do
  [ -e "$f" ] || continue
  if [ -f "${f}.bai" ] || [ -f "${f%.bam}.bai" ]; then
    echo "OK   有索引  $f"
  else
    echo "MISS 缺索引  $f  -> 补建中..."
    start=$(date +%s)
    samtools index -@ 8 "$f" && echo "     完成  $(stat -c%s "${f}.bai" 2>/dev/null) B  用时 $(( $(date +%s) - start )) 秒"
  fi
done

echo
echo "=== 最终清单 ==="
ls -la /home/hugo/data/03_align/
