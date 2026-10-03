#!/usr/bin/env bash
# repair_one.sh <partial_file>
# 把按百分比截断的 gzip 修复成完整 gzip：
#   1) 解压统计总行数（末条 fastq 记录可能残缺）
#   2) 截到 4 的整数倍行（保证每条 record 完整）
#   3) 用 gzip -1 重新压缩为完整 gzip（带合法结尾 CRC/ISIZE）
set -u
f="$1"
base="${f%.partial*}"
tmp="${base}.repaired.gz"

if [ -f "$base" ]; then
  echo "SKIP(已存在成品) $base"
  exit 0
fi

# 1) 统计行数
n=$(gzip -dc "$f" 2>/dev/null | wc -l | tr -d ' ')
if [ -z "$n" ] || [ "$n" -lt 4 ]; then
  echo "FAIL(无有效数据) $f  lines=$n"
  exit 1
fi
full=$(( n / 4 * 4 ))
dropped=$(( n - full ))

# 2)+3) 截断重压
gzip -dc "$f" 2>/dev/null | head -n "$full" | gzip -1 -c > "$tmp"

if [ ! -s "$tmp" ]; then
  echo "FAIL(输出为空) $f"
  rm -f "$tmp"
  exit 1
fi

# 校验：完整 gzip 应通过 gzip -t
if gzip -t "$tmp" 2>/dev/null; then
  mv "$tmp" "$base"
  echo "OK $base  reads=$((full/4))  丢弃残行=$dropped  大小=$(du -h "$base" | cut -f1)"
else
  echo "FAIL(校验不过) $f"
  rm -f "$tmp"
  exit 1
fi
