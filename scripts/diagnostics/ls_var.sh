#!/usr/bin/env bash
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
echo "########## 04_variant 目录 ##########"
ls -la /home/hugo/data/04_variant/
echo
echo "########## 60% 比对进度 ##########"
ps -eo pid,etime,rss,comm --sort=-rss | grep -E "minimap2|samtools" | grep -v grep | head -6
ls -la /home/hugo/data/03_align/SRR12044649_60* 2>/dev/null
echo
echo "########## minimap2 版 Kenya 是否已有 tab ##########"
ls -la /home/hugo/data/tmp/SRR12044649*.tab 2>/dev/null
