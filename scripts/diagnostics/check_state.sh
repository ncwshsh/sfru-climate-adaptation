#!/usr/bin/env bash
# check_state.sh —— 会话开工状态体检（WSL 内运行）
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

echo "=== [1] 当前时间 ==="
date

echo
echo "=== [2] 比对产物验真 (samtools quickcheck) ==="
n_ok=0; n_bad=0
for f in /home/hugo/data/03_align/*.dedup.bam; do
  [ -e "$f" ] || continue
  sz=$(stat -c%s "$f")
  if samtools quickcheck "$f" 2>/dev/null && [ "$sz" -gt 1000000 ]; then
    echo "OK   $(basename "$f")  $((sz/1024/1024)) MB"
    n_ok=$((n_ok+1))
  else
    echo "BAD  $(basename "$f")  $sz B"
    n_bad=$((n_bad+1))
  fi
done
echo "---- 合格 $n_ok 个 / 坏 $n_bad 个 ----"

echo
echo "=== [3] 比对率统计 ==="
for f in /home/hugo/data/03_align/*.flagstat; do
  b=$(basename "$f" .flagstat)
  tot=$(head -1 "$f" | awk '{print $1}')
  map=$(awk '/^[0-9]+ \+ [0-9]+ mapped \(/{print $1" ("$5")"; exit}' "$f")
  echo "$b  total=$tot  mapped=$map"
done

echo
echo "=== [4] WSL 原生盘数据 ==="
echo "-- 01_raw 文件数 / 体积 --"
ls /home/hugo/data/01_raw 2>/dev/null | wc -l
du -sh /home/hugo/data/01_raw 2>/dev/null
echo "-- 完整 fastq.gz(双端齐全的样本) --"
ls /home/hugo/data/01_raw/*_1.fastq.gz 2>/dev/null | wc -l
echo "-- ref --"
ls /home/hugo/data/ref/ 2>/dev/null | head

echo
echo "=== [5] 磁盘 ==="
df -h /home | tail -1

echo
echo "=== [6] 运行中进程 ==="
ps aux | grep -E 'minimap2|samtools|curl|batch_dl' | grep -v grep
echo "(end)"
