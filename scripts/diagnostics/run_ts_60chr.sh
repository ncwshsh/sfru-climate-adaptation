#!/usr/bin/env bash
# run_ts_60chr.sh —— A/B 验收：ref_chr 版 Kenya 60% 的 Ts/Tv 分层
#
# 目的：验证「切到 ref_chr 不改变结论」。严格对拉条件：
#   · 同一个 BAM 输入（SRR12044649 60% 干净 FASTQ）
#   · 同一区域（8 条最大染色体，123 Mb）—— ref_chr 与全量参考的前 8 大都是同 8 条
#   · 同一 mpileup/call 参数（-q20 -Q20 -d 1000）
#   · 唯一变量：比对/调用用的参考（ref_GCF_023101765.2.fna → ref_chr.fna）
#
# 对照基准（全量参考，2026-09-17 04:08）：
#   干净杂合 Ts/Tv = 1.315 (n=780,828) ；干净纯合 1.309 (n=321,328)
#   DP30-45 het/hom = 3.56 ；DP60-90 = 64.3 ；DP>90 = 215.5
export PATH=/home/hugo/mamba/envs/sfru/bin:/usr/bin:/bin:$PATH

REF=/home/hugo/data/ref/ref_chr.fna \
bash /mnt/c/SF_data/tools/ts_deep2.sh \
  /home/hugo/data/03_align/SRR12044649_60chr.dedup.bam \
  SRR12044649_60chr 8 8
