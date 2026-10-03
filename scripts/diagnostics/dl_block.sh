#!/usr/bin/env bash
# dl_block.sh —— 下载单个分块，支持按已下字节续追加（worker，供 dl_ena.sh 用 xargs -P 调用）
#
# 用法: bash dl_block.sh <part_Windows路径> <part_POSIX路径> <start> <end> <url> <proxy>
# 特点: 不用 -C -、也不用 -o，改为 stdout 追加写 -> 断线只丢一个 TCP 连接的尾部，已下字节全部保留
#
# ★ 2026-09-19 修复「块超尺寸」bug（第五轮 BR/FL 卡死 4 轮的根因）：
#   旧版 `curl --retry 3 ... >> part`：传输中断后 curl 内部 retry 会**重发同一个 range**
#   并把完整 range 输出再追加一遍 → part 变成 2×16MB（实测块 17 = 精确 33,554,432 B）
#   → dl_ena.sh 校验 `size == exp` 永远不成立 → 该块被判「未完成」→ 每轮重跑、每轮又超 → 死循环。
#   修法：**去掉 curl 内部 --retry**，改为每次 attempt 写独立临时文件，curl 结束后把
#   tmp 的有效字节追加进 part（失败时保留前缀、下轮 cur 前移）；并加超尺寸保护截断。

export PATH="/usr/bin:/bin:$PATH"

part_w="$1"; part_p="$2"; start="$3"; end="$4"; url="$5"; proxy="$6"
exp=$(( end - start + 1 ))
max_att=60
stall=0

for att in $(seq 1 $max_att); do
  sz=0
  [ -f "$part_p" ] && sz=$(stat -c %s "$part_p")
  if [ "$sz" -ge "$exp" ]; then exit 0; fi

  cur=$(( start + sz ))
  tmp="${part_p}.att"
  rm -f "$tmp"
  # ★ 必须带 -f（--fail）！否则服务器返回 403/404/5xx 时，curl 会把 **HTML 错误页
  #   当数据写进块文件**（2026-09-18 实测：块首是 <title>403 Forbidden</title>）。
  #   ★ 不用 curl 内部 --retry（它是「重发整个 range」语义，配合 >> 会重复追加）；
  #     重试由本脚本外层 attempt 循环负责，每次重新计算 cur。
  curl -fsS -x "$proxy" -r "${cur}-${end}" \
       --max-time 900 --speed-time 120 --speed-limit 512 "$url" > "$tmp" 2>/dev/null

  tsz=0
  [ -f "$tmp" ] && tsz=$(stat -c %s "$tmp")
  if [ "$tsz" -gt 0 ]; then
    # 超尺寸保护：本 attempt 最多补 exp - sz 字节（服务器若忽略 range 只回部分/多余数据时截断）
    allow=$(( exp - sz ))
    if [ "$tsz" -gt "$allow" ]; then
      head -c "$allow" "$tmp" >> "$part_p"
    else
      cat "$tmp" >> "$part_p"
    fi
    stall=0
  fi
  rm -f "$tmp"

  sz2=0
  [ -f "$part_p" ] && sz2=$(stat -c %s "$part_p")
  if [ "$sz2" -le "$sz" ]; then
    stall=$(( stall + 1 ))
    sleep 8
  fi
  if [ "$stall" -ge 10 ]; then
    echo "BLOCKFAIL ${part_w} ${sz2}/${exp}"
    exit 1
  fi
done
echo "BLOCKFAIL ${part_w} max_att"
exit 1
