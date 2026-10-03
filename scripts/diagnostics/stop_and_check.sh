#!/usr/bin/env bash
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

echo "=== 1. 停止残留进程 ==="
pkill -9 minimap2 2>/dev/null; pkill -9 samtools 2>/dev/null
sleep 2
echo "残留: $(pgrep -c minimap2 2>/dev/null || echo 0) minimap2"

echo
echo "=== 2. 清理 tmp ==="
du -sh /home/hugo/data/tmp 2>/dev/null
rm -f /home/hugo/data/tmp/* 2>/dev/null
echo "清理后: $(ls /home/hugo/data/tmp 2>/dev/null | wc -l) 项"

echo
echo "=== 3. 验真所有 dedup.bam（quickcheck + 体积）==="
GOOD=0; BAD=0
for f in /home/hugo/data/03_align/*.dedup.bam; do
  [ -e "$f" ] || continue
  sz=$(stat -c%s "$f")
  if samtools quickcheck "$f" 2>/dev/null && [ "$sz" -gt 1048576 ]; then
    printf "  OK   %-42s %6.2f GB\n" "$(basename "$f")" "$(echo "scale=2;$sz/1073741824" | bc)"
    GOOD=$((GOOD+1))
  else
    printf "  BAD  %-42s %d bytes  -> 删除\n" "$(basename "$f")" "$sz"
    rm -f "$f" "$f.bai"
    BAD=$((BAD+1))
  fi
done
echo "  有效 $GOOD 个 / 删除 $BAD 个"
