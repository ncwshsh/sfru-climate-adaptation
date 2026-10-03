#!/usr/bin/env bash
# angsd_gl.sh —— 用 ANGSD 从 BAM 直接算基因型似然（低深度群体基因组学的入口）
#
# 为什么不做"先 call 变异再分析"：
#   本队列可用深度只有 ~6x（名义 6x × 0.6 ≈ 3.6x），硬叫基因型会把不确定性当成确定，
#   且深度差异会直接变成假的空间结构。**ANGSD 直接吃基因型似然（GL）**，把不确定性
#   一路带到 PCA / RDA，这是低深度数据的正确做法（也是 PCAngsd 的设计前提）。
#
# 用法:
#   bash /mnt/c/SF_data/tools/angsd_gl.sh <输出前缀> [染色体或区间] [线程数]
#   例（试跑，先拿最长染色体量速度）:
#     bash angsd_gl.sh /home/hugo/data/angsd/pilot NC_064236.1 20
#   例（全基因组）:
#     bash angsd_gl.sh /home/hugo/data/angsd/s2_all "" 20
#
# 参数取舍（写在注释里，方便论文方法学直接抄）：
#   -GL 1        SAMtools 似然模型（适合 Illumina/BGISEQ）
#   -doGlf 2     beagle 格式 GL（PCAngsd 的标准输入）
#   -doMajorMinor 1 / -doMaf 1   用似然推断主次等位基因与频率，不依赖参考等位
#   -minMapQ 30 -minQ 20         2026-09-20 定：参考偏倚重，映射质量阈值不放宽
#   -minInd      至少这么多"有数据的个体"才保留位点（默认 = 80% 样本）
#   -SNP_pval    位点多态性的似然比检验阈值，先把非变异位点过滤掉
#   -minMaf      次要等位频率下限，PCA 用 0.05 是通行做法（去掉稀有噪声）
set -uo pipefail

GEA_ENV=/home/hugo/mamba/envs/gea
export PATH=$GEA_ENV/bin:$PATH

OUT=${1:?需要输出前缀}
REG=${2:-}          # 为空 = 全基因组；否则传染色体名或 "chr:start-end"
THR=${3:-20}
BAMLIST=${BAMLIST:-/mnt/c/SF_data/tools/bamlist_keep214.txt}
REF=${REF:-/home/hugo/data/ref/ref_chr.fna}
MININD=${MININD:-171}     # 214 × 0.8
MINMAF=${MINMAF:-0.05}
SNPVAL=${SNPVAL:-1e-6}

mkdir -p "$(dirname "$OUT")"
n=$(wc -l < "$BAMLIST")
echo "===== $(date '+%F %T') ANGSD 开始 ====="
echo "  样本: $n 个（$BAMLIST）"
echo "  区间: ${REG:-全基因组}   线程: $THR"
echo "  minInd=$MININD  minMaf=$MINMAF  SNP_pval=$SNPVAL  minMapQ=30 minQ=20"

RARG=(); [ -n "$REG" ] && RARG=(-r "$REG")

# ★★ -baq 0 且不加 -C（2026-09-22 实测，本项目专属结论）
#    在 NC_064236.1:10.0-10.5 Mb 上对比（214 样本，20 线程）：
#      -baq 1 -C 50 ：76 s，只留 1,981 个位点
#      -baq 1       ：81 s，留 10,287 个位点
#      -baq 0       ：33 s，留 17,138 个位点  ← 又快又全
#    原因：-C 50 会把"错配多的 read"的比对质量压低，而**错配多正是巴西种群分化于参考基因组
#    的直接表现**——用它等于系统性丢掉热带样本的数据，反而制造与纬度同向的技术偏差。
#    BAQ 同理（压低邻近 indel 的碱基质量），且它是为"硬叫基因型"设计的，
#    本队列走的是 ANGSD 似然框架，收益小、代价大。
angsd -b "$BAMLIST" -ref "$REF" \
  -uniqueOnly 1 -remove_bads 1 -only_proper_pairs 1 -trim 0 -baq 0 \
  -minMapQ 30 -minQ 20 -minInd "$MININD" -setMinDepthInd 1 \
  -GL 1 -doGlf 2 -doMajorMinor 1 -doMaf 1 \
  -SNP_pval "$SNPVAL" -minMaf "$MINMAF" \
  -P "$THR" "${RARG[@]}" -out "$OUT"

rc=$?
echo "===== $(date '+%F %T') ANGSD 结束 rc=$rc ====="
ls -la "${OUT}".* 2>/dev/null
exit $rc
