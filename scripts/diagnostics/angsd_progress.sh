#!/usr/bin/env bash
# angsd_progress.sh —— 量一下 ANGSD 跑到哪了、还要多久
# 用法: bash /mnt/c/SF_data/tools/angsd_progress.sh [观测秒数]
export PATH=/home/hugo/mamba/envs/gea/bin:$PATH
LOG=${LOG:-/home/hugo/data/angsd/s2_gl.log}
BEAGLE=${BEAGLE:-/home/hugo/data/angsd/s2_gl.beagle.gz}
W=${1:-180}

pos() { grep -o 'pos:[0-9]*' "$LOG" 2>/dev/null | tail -1 | cut -d: -f2; }
sz()  { stat -c%s "$BEAGLE" 2>/dev/null || echo 0; }

p1=$(pos); s1=$(sz)
sleep "$W"
p2=$(pos); s2=$(sz)
chr=$(grep -o 'chr: NC_[0-9.]*' "$LOG" 2>/dev/null | tail -1 | awk '{print $2}')

echo "当前染色体 : $chr"
echo "观测窗口   : ${W}s"
echo "位点位置   : $p1 -> $p2"
python3 - "$p1" "$p2" "$s1" "$s2" "$W" <<'PY'
import sys
p1, p2, s1, s2, w = [float(x) for x in sys.argv[1:6]]
d = (p2 - p1) / w
print("推进速度   : %.0f kb/min" % (d * 60 / 1000))
if d > 0:
    print("预计剩余   : %.1f 小时（全基因组 381.8 Mb）" % ((381.8e6 - p2) / d / 3600))
print("beagle 增长: %.1f MB/min" % ((s2 - s1) / 1048576 / w * 60))
if p2 > 0:
    print("beagle 终体积外推: %.1f GB" % (s2 * (381.8e6 / p2) / 1024**3))
PY
echo "--- 进程 ---"
ps -eo pid,etime,pcpu,cmd | grep "[a]ngsd -b" | awk '{print "  CPU="$3"%  用时="$2}'
free -g | sed -n 2p
