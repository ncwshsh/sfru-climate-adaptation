#!/usr/bin/env bash
# dl_wc.sh —— 分块并发下载 WorldClim（单线程只有 21 KB/s，会被拖死）
#
# 背景：ucdavis 服务器经代理单线程约 21 KB/s，一个 50 MB 的包要 40 分钟。
# 之前下 FASTQ 的实测：8 并发可到 0.911 MB/s、16 并发 1.821 MB/s（单线程 0.245）。
# 所以这里照搬"分块 + 并发"的思路。
#
# ⚠️ 两个必须遵守的坑（都是本项目踩过的）：
#   1. `curl --retry` + `>>` 是反模式：重试会把整个区间重发一遍再追加，块体积翻倍、永远校验不过
#      ⇒ 重试由本脚本自己算当前已下字节（cur），每次 attempt 写独立 tmp 再追加
#   2. 每块的追加前必须重算 cur，不能只看文件是否存在
#
# 用法: bash /mnt/c/SF_data/tools/dl_wc.sh <url> <输出文件> [并发数]
set -uo pipefail

U=${1:?需要 URL}
OUT=${2:?需要输出文件}
N=${3:-16}
export http_proxy=${http_proxy:-http://127.0.0.1:8830}
export https_proxy=${https_proxy:-http://127.0.0.1:8830}

echo "===== $(date '+%F %T') 分块下载 $U ====="
SIZE=$(timeout 60 curl -sIL "$U" | grep -i '^content-length' | tail -1 | tr -d '\r' | awk '{print $2}')
[ -n "$SIZE" ] || { echo "取不到文件大小"; exit 1; }
echo "  总大小: $((SIZE/1024/1024)) MB   并发: $N"
CH=$(( (SIZE + N - 1) / N ))

dl_one() {
  local i=$1
  local st=$((i * CH)); local en=$((st + CH - 1))
  [ "$en" -ge "$SIZE" ] && en=$((SIZE - 1))
  local len=$((en - st + 1))
  local part=$(printf "%s.part%03d" "$OUT" "$i")   # ★ 必须零填充：否则 cat part* 按字典序合并会错乱
  local cur=0
  [ -s "$part" ] && cur=$(stat -c%s "$part")
  if [ "$cur" -ge "$len" ]; then echo "  块 $i 已完成 ($cur/$len)"; return 0; fi
  local try=0
  while [ "$cur" -lt "$len" ] && [ "$try" -lt 4 ]; do
    try=$((try + 1))
    local from=$((st + cur))
    timeout 600 curl -sL -r "${from}-${en}" -o "${part}.tmp" "$U"
    if [ -s "${part}.tmp" ]; then
      cat "${part}.tmp" >> "$part"
      rm -f "${part}.tmp"
    fi
    cur=0; [ -s "$part" ] && cur=$(stat -c%s "$part")
  done
  if [ "$cur" -ne "$len" ]; then echo "  块 $i 未完成 ($cur/$len)"; return 1; fi
  echo "  块 $i 完成 ($cur)"
  return 0
}
export -f dl_one
export U OUT SIZE CH

seq 0 $((N - 1)) | xargs -P "$N" -I {} bash -c 'dl_one {}'

# 合并（按数字序，绝不按 glob 字典序）
echo "--- 合并 ---"
: > "$OUT"
for i in $(seq 0 $((N - 1))); do
  p=$(printf "%s.part%03d" "$OUT" "$i")
  [ -s "$p" ] && cat "$p" >> "$OUT"
done
GOT=$(stat -c%s "$OUT" 2>/dev/null || echo 0)
echo "  合并后: $GOT / $SIZE"
MAGIC=$(head -c 4 "$OUT" | od -An -tx1 | tr -d ' \n')
echo "  文件头: $MAGIC （zip 应为 504b0304）"
if [ "$MAGIC" != "504b0304" ]; then
  echo "  ❌ 不是 zip！多半是合并顺序错了或下到错误页"
fi
if [ "$GOT" -eq "$SIZE" ] && [ "$MAGIC" = "504b0304" ]; then
  rm -f "${OUT}".part*
  echo "  ✅ 大小一致，已清理分块"
else
  echo "  ⚠ 大小不一致，保留分块以便续跑（再跑一次本脚本即可续传）"
fi
