#!/usr/bin/env bash
echo "=== 比对：已完成的 dedup.bam ==="
ls -la --time-style=+%H:%M /home/hugo/data/03_align/*.dedup.bam 2>/dev/null
echo
echo "=== 正在处理的样本（tmp 中有文件的）==="
ls /home/hugo/data/tmp/ 2>/dev/null | sed 's/_[sc]\././; s/\.bam$//' | sed 's/\.[0-9]*$//' | sort -u
echo
echo "=== 当前进程 ==="
ps -eo pcpu,etime,comm --sort=-pcpu | head -8
echo
echo "=== tmp 占用 ==="
du -sh /home/hugo/data/tmp 2>/dev/null
