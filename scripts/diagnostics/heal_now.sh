#!/usr/bin/env bash
# heal_now.sh —— 在 dl_ena.sh「无进程在读」的间隙打自愈补丁，并清掉已知坏样本的残块
#
# 为什么挑间隙：bash 是按文件偏移续读脚本的，边跑边改会让正在跑的实例读到错位内容。
# 所以这里轮询到没有任何 dl_ena.sh 进程的瞬间立刻改（改完 <1 s，下一个实例启动时已改好）。
#
# 用法: bash /c/SF_data/tools/heal_now.sh

export PATH="/usr/bin:/bin:$PATH"
TOOLS=/c/SF_data/tools
RAW=/c/SF_data/01_raw
PY="C:/Users/Admin/.workbuddy/binaries/python/versions/3.13.12/python.exe"

echo "[$(date '+%m-%d %H:%M:%S')] 等待 dl_ena.sh 空闲窗口…"
n=0
while [ "$(ps -ef 2>/dev/null | grep -c '[d]l_ena.sh')" -gt 0 ]; do
  sleep 2; n=$((n+1))
  if [ "$n" -gt 900 ]; then echo "!! 等了 30 分钟仍无窗口，放弃（下次手工重跑本脚本）"; exit 3; fi
done

echo "[$(date '+%m-%d %H:%M:%S')] 窗口出现，打补丁"
"$PY" "C:/SF_data/tools/patch_dl_ena_selfheal.py"
rc=$?
if [ "$rc" != "0" ]; then echo "!! 补丁失败 rc=$rc"; exit 4; fi

echo "[$(date '+%m-%d %H:%M:%S')] 校验补丁已落地"
grep -c "自愈补丁（2026-09-18 夜间）" "$TOOLS/dl_ena.sh"

echo "[$(date '+%m-%d %H:%M:%S')] 清理已知坏样本的残块（尺寸达标但内容错，留着会被复用）"
cd "$RAW" || exit 1
for base in SRR34858474_1.fastq.gz.partial15 SRR9289285_1.fastq.gz.partial10; do
  cnt=$(ls ${base}.part* 2>/dev/null | wc -l)
  if [ "$cnt" -gt 0 ]; then
    ls ${base}.part* | xargs -n 40 rm -f 2>/dev/null
    echo "  已清 ${base}.part*（${cnt} 个）"
  else
    echo "  ${base}.part* 无残留（已清过或本就干净）"
  fi
done

echo "[$(date '+%m-%d %H:%M:%S')] 剩余 .bad 隔离：$(ls "$RAW"/.bad.* 2>/dev/null | wc -l) 个"
exit 0
