#!/usr/bin/env bash
# probe_beagle.sh —— 诊断 beagle 里 marker 的命名与位置范围
set -uo pipefail
B=/home/hugo/data/angsd/beagle_1M.beagle.gz
echo "=== 前 3 个 marker ==="
zcat "$B" | sed -n '2,4p' | cut -d' ' -f1
echo
echo "=== NC_064236.1 的位点统计 ==="
zcat "$B" | tail -n +2 | cut -d' ' -f1 | grep '^NC_064236\.1_' > /tmp/c236.txt
echo "  位点数: $(wc -l < /tmp/c236.txt)"
echo "  位置范围:"
awk -F_ '{print $2}' /tmp/c236.txt | sort -n | sed -n '1p;$p' | tr '\n' ' '; echo
echo
echo "=== 8.18-8.20 Mb 区间到底有没有位点 ==="
awk -F_ '$2>=8180000 && $2<=8200000' /tmp/c236.txt | wc -l
echo "=== 6.86-6.88 Mb 区间 ==="
awk -F_ '$2>=6860000 && $2<=6880000' /tmp/c236.txt | wc -l
echo
echo "=== 附近的位点示例（8.0-8.5 Mb）==="
awk -F_ '$2>=8000000 && $2<=8500000 {print}' /tmp/c236.txt | head -5
