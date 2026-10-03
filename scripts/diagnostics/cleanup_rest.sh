#!/bin/bash
# 续删剩余冗余块/残片，分批 40，带进度日志
export PATH="/usr/bin:/bin:$PATH"
LIST=/c/SF_data/tools/delete_list.txt
LOG=/c/SF_data/tools/cleanup_rest.log
: > "$LOG"

total=0; done_n=0; fail_n=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  total=$((total+1))
done < "$LIST"

echo "[$(date +%H:%M:%S)] 清单总条目 = $total" | tee -a "$LOG"

batch=(); bcount=0
flush() {
  [ ${#batch[@]} -eq 0 ] && return
  # 转成 Windows 路径
  win=()
  for p in "${batch[@]}"; do win+=("$(printf '%s' "$p" | sed 's|^/c/|C:/|')"); done
  rm -f "${win[@]}" 2>>"$LOG"
  bcount=$((bcount+1))
  if [ $((bcount % 25)) -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] 批 $bcount 已发 (累计约 $((bcount*40)) 个)" | tee -a "$LOG"
  fi
  batch=()
}

while IFS= read -r line; do
  [ -z "$line" ] && continue
  batch+=("$line")
  if [ ${#batch[@]} -ge 40 ]; then flush; fi
done < "$LIST"
flush

echo "[$(date +%H:%M:%S)] 批量删除阶段结束，共 $bcount 批" | tee -a "$LOG"

# 复查剩余
left=$(sed 's|^/c/|C:/|' "$LIST" | xargs -r -n 200 ls -1 2>/dev/null | wc -l)
echo "[$(date +%H:%M:%S)] 清单中仍存在 = $left" | tee -a "$LOG"
echo "[$(date +%H:%M:%S)] 01_raw = $(ls -1 /c/SF_data/01_raw | wc -l) 条, 01_deep = $(ls -1 /c/SF_data/01_deep | wc -l) 条" | tee -a "$LOG"
echo "=== cleanup done ===" | tee -a "$LOG"
