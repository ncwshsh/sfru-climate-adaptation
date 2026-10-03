#!/usr/bin/env bash
# ==============================================================================
# 把 WSL 里的 ANGSD beagle 中间产物备份到 Windows 侧，并做完整性校验
#
# 用法（在 Windows PowerShell 或 CMD 里）：
#   wsl -d Ubuntu-24.04 -- bash /mnt/c/SF_data/tools/backup_beagle.sh
#
# 说明：
#   - 目标 $DST 在 C 盘，可用空间充足（922 GB）
#   - /mnt/c 写入约 48 MB/s，8 GB 约 3 分钟
#   - 末尾用 `gzip -t` 全量读一遍校验，确认没有静默损坏
#   - 已存在且大小一致的文件会跳过（可反复跑）
# ==============================================================================

set -u

SRC=/home/hugo/data/angsd
DST=/mnt/c/SF_data/00_wsl_backup
FILES="s2_gl.beagle.gz strain_markers.beagle.gz"

echo "=============================================="
echo "源目录: $SRC"
echo "目标  : $DST"
echo "=============================================="

echo
echo "== 1) 源文件是否存在（先确认 vhdx 压缩没弄丢东西）=="
if [ ! -d "$SRC" ]; then
  echo "  !! 源目录不存在: $SRC"
  exit 1
fi
ls -l "$SRC"/*.beagle.gz 2>&1

echo
echo "== 2) 逐个拷贝 =="
mkdir -p "$DST" || { echo "  !! 无法创建 $DST"; exit 1; }

for f in $FILES; do
  s="$SRC/$f"
  d="$DST/$f"
  if [ ! -f "$s" ]; then
    echo "  [跳过] 源文件不存在: $f"
    continue
  fi
  ss=$(stat -c%s "$s")
  if [ -f "$d" ] && [ "$(stat -c%s "$d")" = "$ss" ]; then
    echo "  [已有] $f  大小一致（$(numfmt --to=iec $ss 2>/dev/null || echo $ss)B），跳过"
    continue
  fi
  echo "  [拷贝] $f  ($(numfmt --to=iec $ss 2>/dev/null || echo $ss)B) ..."
  cp -v "$s" "$d" || echo "  !! 拷贝失败: $f"
done

echo
echo "== 3) 完整性校验（gzip -t 全量读，慢但可靠）=="
fail=0
for f in $FILES; do
  d="$DST/$f"
  [ -f "$d" ] || continue
  printf '  %-30s ' "$f"
  if gzip -t "$d" 2>/dev/null; then
    echo "OK   $(stat -c%s "$d") bytes"
  else
    echo "FAIL 损坏！"
    fail=1
  fi
done

echo
echo "== 4) Windows 侧落地清单 =="
ls -l "$DST"

echo
if [ "$fail" = "0" ]; then
  echo ">>> 全部校验通过"
else
  echo ">>> 有文件校验失败，请看上面 FAIL 行"
fi

# 备注：$SRC 下还有 beagle_1M.beagle.gz / beagle_200k.beagle.gz（抽稀版本，
#       可由 s2_gl 重新生成），需要一起备份就把它们加到上面的 FILES 变量。
