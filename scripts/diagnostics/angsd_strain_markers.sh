#!/usr/bin/env bash
# angsd_strain_markers.sh —— 提取经典株系标记基因区域的基因型似然（全部 220 样本）
#
# 为什么用这两个基因（而不是全基因组）：
#   草地贪夜蛾玉米型/水稻型的分子分型，文献标准做法是 **Tpi**（磷酸丙糖异构酶）
#   与 COI（线粒体）。但本项目比对时**剔除了线粒体**（ref_chr 只含 31 条核染色体），
#   COI 路线不可用；所以核基因标记只剩 Tpi，另加同为经典标记的 **Flightin** 作交叉印证。
#   两者都在 NC_064236.1 上（见 09-23 从 GFF 查到的坐标）。
#
# 用全 220 样本（而非 214）：本步骤要给"非美国样本"分型，被剔除的 6 个巴西样本也一并纳入统计，
# 只是为了后续分析时再排除。
set -uo pipefail
export PATH=/home/hugo/mamba/envs/gea/bin:$PATH

REF=/home/hugo/data/ref/ref_chr.fna
BAM=/mnt/c/SF_data/tools/bamlist_all220.txt
OUT=${OUT:-/home/hugo/data/angsd/strain_markers}
RF=/home/hugo/data/angsd/strain_regions.txt
mkdir -p /home/hugo/data/angsd
printf "NC_064236.1\t8180000\t8200000\nNC_064236.1\t6860000\t6880000\n" > "$RF"
cat "$RF"
echo "===== $(date '+%F %T') 提取株系标记区 ====="

angsd -b "$BAM" -ref "$REF" -rf "$RF" \
  -uniqueOnly 1 -remove_bads 1 -only_proper_pairs 1 -trim 0 -baq 0 \
  -minMapQ 30 -minQ 20 -minInd 50 -setMinDepthInd 1 \
  -GL 1 -doGlf 2 -doMajorMinor 1 -doMaf 1 \
  -P 8 -out "$OUT"

echo "===== $(date '+%F %T') 完成 ====="
ls -la "$OUT".* 2>/dev/null
echo "  位点数: $(( $(zcat "$OUT.beagle.gz" | wc -l) - 1 ))"
