#!/usr/bin/env bash
# watch_and_heal.sh —— 夜间无人值守自愈守卫
#
# 背景：2026-09-18 夜间发现 dl_ena.sh 一个自愈缺口——
#   结构校验失败（4 行组首行非 @）时只把成品隔离成 .bad.*，**不清理 .partN 块**；
#   而这些块「尺寸都对」，重跑时会因 `size >= exp` 被直接复用 →
#   拼出同样的坏内容 → 再次 .bad → 死循环，人工不介入永远好不了。
#
# 本脚本：
#   1) 等链 BR 模块结束（此刻 dl_ena.sh 没在被任何进程读 → 改脚本安全）
#   2) 应用补丁 patch_dl_ena_selfheal.py（bad 分支清 .partN）
#   3) 清掉当前已经坏掉的那个样本的残块 SRR9289285_1.part*（720 MB 重新下）
#   4) 等整条链跑完（"全部模块跑完" 出现在 dl_chain.log）
#   5) 备份各模块日志为 *.round2，然后**重跑一遍整链**做第三轮补齐（幂等，零浪费）
#
# 用法: bash /c/SF_data/tools/watch_and_heal.sh > /c/SF_data/tools/watch_and_heal.log 2>&1

export PATH="/usr/bin:/bin:$PATH"
TOOLS=/c/SF_data/tools
RAW=/c/SF_data/01_raw
CHAIN=$TOOLS/dl_chain.log
WLOG=$TOOLS/watch_and_heal.log

say() { printf '[%s] %s\n' "$(date '+%m-%d %H:%M:%S')" "$*" | tee -a "$WLOG"; }

say "========= 自愈守卫启动 ========="

# ---------- 1. 等 BR 模块结束（或整链已跑完） ----------
while : ; do
  if grep -q "模块 BR 结束" "$CHAIN" 2>/dev/null; then say "检测到『模块 BR 结束』，进入修复"; break; fi
  if grep -q "全部模块跑完" "$CHAIN" 2>/dev/null; then say "检测到整链已跑完，直接修复"; break; fi
  sleep 60
done

# ---------- 2. 保证没有任何 dl_ena.sh 正在跑 ----------
n=0
while [ "$(ps -ef 2>/dev/null | grep -c '[d]l_ena.sh')" -gt 0 ]; do
  sleep 20; n=$((n+1))
  [ "$n" -gt 90 ] && { say "!! 等了 30 分钟仍有 dl_ena.sh 在跑，放弃等待，直接修补"; break; }
done

# ---------- 3. 应用补丁 ----------
"C:/Users/Admin/.workbuddy/binaries/python/versions/3.13.12/python.exe" "$TOOLS/patch_dl_ena_selfheal.py" >> "$WLOG" 2>&1
say "补丁已应用（详见 patch 输出）"

# ---------- 4. 清掉已知坏样本的残块（让下一轮能真正重下） ----------
cd "$RAW" || exit 1
for base in SRR9289285_1.fastq.gz.partial10 SRR9289285_2.fastq.gz.partial10; do
  cnt=$(ls ${base}.part* 2>/dev/null | wc -l)
  if [ "$cnt" -gt 0 ]; then
    ls ${base}.part* | xargs -n 40 rm -f 2>/dev/null
    say "已清 ${base}.part* （${cnt} 个）"
  fi
done
# _2 是好的（md5/结构都没问题），但重做一遍更省心？——不，保留 _2，只补 _1
rm -f "${RAW}/.blocks_SRR9289285_1.txt" 2>/dev/null

# ---------- 5. 等整链跑完 ----------
while : ; do
  if grep -q "全部模块跑完" "$CHAIN" 2>/dev/null; then say "整链已跑完，开始第三轮补齐"; break; fi
  sleep 120
done

# ---------- 6. 备份第二轮日志 ----------
cd "$TOOLS" || exit 1
for m in US BR AF AM CN FL; do
  [ -f "dl_${m}.log" ] && cp "dl_${m}.log" "dl_${m}.log.round2"
done
cp "$CHAIN" "${CHAIN%.log}.round2"
say "第二轮日志已备份为 *.round2"

# ---------- 7. 第三轮补齐（幂等：只补缺口，不重复下载） ----------
say "########## 第三轮补齐开始 ##########"
bash "$TOOLS/run_clean.sh" "$TOOLS/dl_chain_s2.sh" > /dev/null 2>&1
rc=$?
say "第三轮补齐结束｜rc=$rc"

# ---------- 8. 汇总 ----------
say "========= 收尾对账 ========="
echo "--- 各模块 ---" | tee -a "$WLOG"
for m in US BR AF AM CN FL; do
  if [ -f "dl_${m}.log" ]; then
    echo "  $m  成功 $(grep -c '结束，退出码=0' dl_${m}.log)｜失败 $(grep -c '结束，退出码=1' dl_${m}.log)｜错误 $(grep -c '\[ERR\]' dl_${m}.log)" | tee -a "$WLOG"
  fi
done
echo "  .bad 隔离文件: $(ls "$RAW"/.bad.* 2>/dev/null | wc -l)" | tee -a "$WLOG"
echo "  01_raw: $(du -sh "$RAW" | cut -f1)｜磁盘余: $(df -h /c | tail -1 | awk '{print $4}')" | tee -a "$WLOG"
say "========= 自愈守卫完成 ========="
