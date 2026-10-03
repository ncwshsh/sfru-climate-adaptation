#!/usr/bin/env bash
# dl_chain_s2.sh —— 串行跑完 S2 队列全部模块（US → BR → AF → AM → CN → FL）
#
# 设计要点：
#  1. **串行**，不并发跨模块（带宽只有 ~2 MB/s，并发只会互相抢）
#  2. **幂等**：dl_ena.sh 会跳过已完成样本（凭证 / md5 双判据）⇒ 重跑零成本，
#     所以 US 放在最前面顺带把第二轮缺口补掉
#  3. 每模块独立日志 dl_<MOD>.log，总日志 dl_chain.log（便于定位是哪一步出问题）
#  4. 单模块失败**不中断**整条链（继续下一个）；退出码与成功/失败计数写进总日志
#
# 用法: bash /c/SF_data/tools/run_clean.sh /c/SF_data/tools/dl_chain_s2.sh

export PATH="/usr/bin:/bin:$PATH"
cd /c/SF_data/tools || exit 1

CHAIN_LOG=/c/SF_data/tools/dl_chain.log
T0=$(date +%s)

say() { printf '[%s] %s\n' "$(date '+%m-%d %H:%M:%S')" "$*" | tee -a "$CHAIN_LOG"; }

say "================ S2 队列串联下载开始 ================"

for MOD in US BR AF AM CN FL; do
  SCRIPT="/c/SF_data/tools/dl_s2/dl_${MOD}.sh"
  MLOG="/c/SF_data/tools/dl_${MOD}.log"

  if [ ! -f "$SCRIPT" ]; then
    say "!! 模块 $MOD 脚本缺失：$SCRIPT —— 跳过"
    continue
  fi

  say "########## 模块 $MOD 开始 ##########"
  MS=$(date +%s)
  bash "$SCRIPT" > "$MLOG" 2>&1
  rc=$?
  ME=$(date +%s)

  ok=$(grep -c '结束，退出码=0' "$MLOG" 2>/dev/null || echo 0)
  bad=$(grep -c '结束，退出码=1' "$MLOG" 2>/dev/null || echo 0)
  err=$(grep -c '\[ERR\]' "$MLOG" 2>/dev/null || echo 0)
  binbad=$(ls /c/SF_data/01_raw/.bad.* 2>/dev/null | wc -l)

  say "模块 $MOD 结束｜rc=$rc｜成功 $ok｜失败 $bad｜错误行 $err｜隔离 .bad $binbad｜耗时 $(( (ME-MS)/60 )) 分钟"
done

say "================ 全部模块跑完，总耗时 $(( ($(date +%s)-T0)/3600 )) 小时 $(( (($(date +%s)-T0)%3600)/60 )) 分 ================"
