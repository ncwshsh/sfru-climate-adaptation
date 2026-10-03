#!/usr/bin/env bash
# 校验 bwa 对照 BAM，并顺带报告 60% 比对进度
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
A=/home/hugo/data/03_align
B=$A/SRR12044649.bwa.dedup.bam

echo "########## bwa 对照 BAM ##########"
ls -la "$B" 2>/dev/null || echo "文件不存在"
if [ -s "$B" ]; then
  if samtools quickcheck -v "$B" 2>/dev/null; then echo "quickcheck: OK"; else echo "quickcheck: 失败或仍在写入"; fi
  echo "--- flagstat 前 8 行 ---"
  samtools flagstat "$B" 2>/dev/null | head -8
  echo "--- mapped reads ---"
  samtools idxstats "$B" 2>/dev/null | awk '{m+=$3} END{print "mapped="m}'
fi

echo
echo "########## bwa 脚本进程 ##########"
ps -eo pid,etime,comm,args --sort=-rss | grep -E "align_bwa_one|bwa mem" | grep -v grep || echo "bwa 脚本已结束"

echo
echo "########## 60% 比对进度 ##########"
ls -la $A/SRR12044649_60* 2>/dev/null
ps -eo pid,etime,rss,comm,args --sort=-rss | grep -E "minimap2|samtools" | grep -v grep | head -8
