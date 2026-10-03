#!/usr/bin/env bash
# watch_round3.sh —— 等整链跑完后自动跑第三轮补齐（幂等）
#
# 背景：第二轮有 4 个样本需要补：
#   BR: SRR9289285（结构坏，块已清）、SRR9289294（缺块，可续传）、SRR9289268
#   AF: SRR34858474（结构坏，66 块已清）
# dl_ena.sh 幂等：已完成的跳过，缺口重下/续传。
#
# 用法: bash /c/SF_data/tools/watch_round3.sh

export PATH="/usr/bin:/bin:$PATH"
TOOLS=/c/SF_data/tools
RAW=/c/SF_data/01_raw
CHAIN=$TOOLS/dl_chain.log
WLOG=$TOOLS/watch_round3.log

say() { printf '[%s] %s\n' "$(date '+%m-%d %H:%M:%S')" "$*" | tee -a "$WLOG"; }

say "========= 第三轮守卫启动 ========="

# 等链结束（"全部模块跑完" 出现在总日志）
n=0
while : ; do
  grep -q "全部模块跑完" "$CHAIN" 2>/dev/null && { say "检测到整链结束"; break; }
  sleep 120
  n=$((n+1))
  if [ "$n" -gt 360 ]; then say "!! 等了 12 小时链仍未结束，守卫退出（人工处理）"; exit 5; fi
done

# 备份第二轮日志
cd "$TOOLS" || exit 1
for m in US BR AF AM CN FL; do
  [ -f "dl_${m}.log" ] && cp "dl_${m}.log" "dl_${m}.log.round2"
done
cp "$CHAIN" "${CHAIN%.log}.round2"
say "第二轮日志已备份为 *.round2"

# 第三轮（幂等补齐）
say "########## 第三轮补齐开始 ##########"
bash "$TOOLS/run_clean.sh" "$TOOLS/dl_chain_s2.sh" > /dev/null 2>&1
rc=$?
say "第三轮补齐结束｜rc=$rc"

# 汇总
say "========= 第三轮对账 ========="
for m in US BR AF AM CN FL; do
  if [ -f "dl_${m}.log" ]; then
    say "  $m  成功 $(grep -c '结束，退出码=0' dl_${m}.log)｜失败 $(grep -c '结束，退出码=1' dl_${m}.log)｜错误 $(grep -c '\[ERR\]' dl_${m}.log)"
  fi
done
say "  .bad 隔离: $(ls "$RAW"/.bad.* 2>/dev/null | wc -l) 个"
say "  01_raw: $(du -sh "$RAW" | cut -f1)｜磁盘余: $(df -h /c | tail -1 | awk '{print $4}')"
say "========= 第三轮守卫完成 ========="
