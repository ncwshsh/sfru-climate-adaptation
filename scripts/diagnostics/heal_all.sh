#!/bin/bash
# heal_all.sh —— 批量就地裁尾 01_raw / 01_deep 中所有未裁尾的按比例下载残片
# 用法: bash heal_all.sh          （默认并发 2 × 每进程 8 线程）
#       PAR=3 TH=6 bash heal_all.sh
export PATH="/usr/bin:/bin:$PATH"

PIGZ="${PIGZ:-$HOME/opt/pigz_root/usr/bin/pigz}"
LIST=/mnt/c/SF_data/tools/heal_list.txt
LOG=/mnt/c/SF_data/tools/heal_run.log
DIRS="/mnt/c/SF_data/01_raw /mnt/c/SF_data/01_deep"
PAR="${PAR:-2}"
TH="${TH:-8}"

[ -x "$PIGZ" ] || { echo "[ERR] 找不到 pigz: $PIGZ"; exit 1; }

# ---- 生成清单（排除隐藏文件、块文件、已裁尾） ----
: > "$LIST"
for D in $DIRS; do
  for f in "$D"/*.fastq.gz.partial* "$D"/*.fq.gz.partial*; do
    [ -f "$f" ] || continue
    b="$(basename "$f")"
    case "$b" in .*) continue ;; esac
    case "$b" in *.part[0-9]|*.part[0-9][0-9]|*.part[0-9][0-9][0-9]) continue ;; esac
    [ -f "${f}.nrec" ] && continue
    echo "$f" >> "$LIST"
  done
done

n=$(grep -c . "$LIST")
tb=$(xargs -d '\n' -r stat -c %s < "$LIST" 2>/dev/null | awk '{s+=$1} END{print s+0}')
echo "[$(date +%H:%M:%S)] 待治 $n 个文件，合计 $(awk -v b="$tb" 'BEGIN{printf "%.2f GB", b/1073741824}')" | tee -a "$LOG"
echo "[$(date +%H:%M:%S)] pigz=$("$PIGZ" --version 2>&1 | head -1)｜并发=$PAR｜每进程线程=$TH" | tee -a "$LOG"

# ---- 批量执行 ----
xargs -d '\n' -r -P "$PAR" -n 1 bash /mnt/c/SF_data/tools/heal_one.sh < "$LIST" 2>&1 | tee -a "$LOG"

# ---- 复查 ----
echo "" | tee -a "$LOG"
echo "[$(date +%H:%M:%S)] === 复查 ===" | tee -a "$LOG"
left=0
for D in $DIRS; do
  for f in "$D"/*.fastq.gz.partial* "$D"/*.fq.gz.partial*; do
    [ -f "$f" ] || continue
    b="$(basename "$f")"
    case "$b" in .*) continue ;; esac
    case "$b" in *.part[0-9]*) continue ;; esac
    [ -f "${f}.nrec" ] || left=$((left+1))
  done
done
echo "仍未裁尾     = $left" | tee -a "$LOG"
echo "01_raw 成品数 = $(ls -1 /mnt/c/SF_data/01_raw/*.fastq.gz 2>/dev/null | wc -l)" | tee -a "$LOG"
echo "01_raw 条目数 = $(ls -1a /mnt/c/SF_data/01_raw | wc -l)" | tee -a "$LOG"
echo "01_deep 条目数 = $(ls -1a /mnt/c/SF_data/01_deep | wc -l)" | tee -a "$LOG"
echo "=== heal done ===" | tee -a "$LOG"
