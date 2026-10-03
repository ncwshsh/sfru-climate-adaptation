#!/usr/bin/env bash
# resume_after_reboot.sh —— 重启电脑后一键恢复：环境自检 + 继续 S2 全队列 -k15 比对
#
# 用法（Windows Git Bash 侧；长任务必须用工具 background 持有）:
#   bash /c/SF_data/tools/resume_after_reboot.sh
#
# 2026-09-20 重写说明：旧版针对的是「下载阶段 + minimap2 比对」，已全部过时。
#   - 下载已于 2026-09-19 全队列 220/220 完成，本脚本不再碰下载
#   - 比对器已定为 bwa mem（-k15），参考固定 ref_chr（31 条核染色体）
#   - 比对**不需要网络/代理**，只需 WSL 与 ref_chr 索引
#   - 全流程幂等：已有 <SRR>.k15.dedup.bam + .bai 的样本自动跳过，中断多少次都不重复劳动
set -uo pipefail
export PATH="/usr/bin:/bin:$PATH"

TOOLS=/c/SF_data/tools
ALN=/c/SF_data/03_align
echo "[$(date '+%F %T')] ======== 重启后恢复自检 ========"

# 1. WSL 可用性
if ! wsl -d Ubuntu-24.04 -e bash -c 'echo ok' < /dev/null 2>/dev/null | grep -q ok; then
  echo "[FATAL] WSL 不可用（重启后可能需先手动启动一次：wsl -d Ubuntu-24.04）"; exit 1
fi
echo "  WSL ✅"

# 2. 参考索引（必须恰好 31 条核染色体）
ok_ref=$(wsl -d Ubuntu-24.04 -e bash -c '
  [ -s /home/hugo/data/ref/ref_chr.fna.fai ] && echo "fai=$(wc -l < /home/hugo/data/ref/ref_chr.fna.fai)" || echo "MISSING"' < /dev/null 2>&1 | tail -1)
echo "  参考: $ok_ref（应为 fai=31）"
case "$ok_ref" in fai=31) ;; *) echo "[FATAL] ref_chr 索引异常"; exit 1;; esac

# 3. 进度与容量
echo "  k15 BAM 已有: $(ls "$ALN"/*.k15.dedup.bam 2>/dev/null | wc -l) 个（会被跳过）"
echo "  队列总数    : $(( $(wc -l < "$TOOLS/cohort_formal_s2.tsv") - 1 )) 个"
echo "  磁盘余量    : $(df -h /c | tail -1 | awk '{print $4}')"

# 4. 启动（前台阻塞 → 由调用方用 background 持有）
echo "[$(date '+%F %T')] 启动全队列 -k15 比对…"
wsl -d Ubuntu-24.04 -e bash /mnt/c/SF_data/tools/run_align_s2.sh < /dev/null
echo "[$(date '+%F %T')] ======== 比对结束 ========"
