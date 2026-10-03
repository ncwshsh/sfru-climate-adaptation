#!/usr/bin/env bash
# build_chr_ref.sh —— 从完整参考里抽出 31 条 NC_ 染色体，另建一份干净参考 + 双索引
#
# 为什么：38 条 NW_ scaffold 只占基因组 0.56% 碱基，却吃掉 6.1% 的 reads；
#         NW_026095720.1（44 kb）raw 深度 8,409×，是塌缩重复阵列，必须从比对目标里剔除。
# 产物（不删旧文件，旧的继续可用）：
#   ref/ref_chr.fna                31 条 NC_ 染色体，381,761,283 bp
#   ref/ref_chr.fna.{amb,ann,bwt,pac,sa}   bwa 索引（前缀必须等于 FASTA 全名）
#   ref/ref_chr.fna.mmi             minimap2 索引
# 用法: wsl -d Ubuntu-24.04 -- bash /mnt/c/SF_data/tools/build_chr_ref.sh < /dev/null
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

REFDIR=/home/hugo/data/ref
OLD=$REFDIR/ref_GCF_023101765.2.fna
NEW=$REFDIR/ref_chr.fna
LOG=$REFDIR/build_chr_ref.log
exec > >(tee -a "$LOG") 2>&1

echo "=== start $(date '+%F %T') ==="
[ -s "${OLD}.fai" ] || { echo "[ERR] 缺 ${OLD}.fai"; exit 1; }

CHRS=$(awk '$2>1000000 {print $1}' "${OLD}.fai")
echo "选中 $(printf '%s\n' $CHRS | wc -l) 条染色体级序列"
printf '%s\n' "$CHRS" > "$REFDIR/chr_list.txt"

TOT=$(awk '$2>1000000 {s+=$2} END{print s}' "${OLD}.fai")
echo "预期总长 = $TOT bp"

if [ ! -s "$NEW" ]; then
  samtools faidx "$OLD" $CHRS > "${NEW}.tmp" || { echo "[ERR] faidx 失败"; exit 1; }
  mv "${NEW}.tmp" "$NEW"
fi
samtools faidx "$NEW"
GOT=$(awk '{s+=$2} END{print s}' "${NEW}.fai")
NSEQ=$(wc -l < "${NEW}.fai")
echo "实际: $NSEQ 条  总长 $GOT bp"
[ "$GOT" = "$TOT" ] && echo "✅ 总长吻合" || echo "⚠️ 总长不符（exp=$TOT got=$GOT）"

echo
echo "--- bwa 索引 $(date '+%T') ---"
if [ ! -s "${NEW}.bwt" ]; then
  bwa index "$NEW" 2>&1 | tail -3
else
  echo "已存在，跳过"
fi

echo
echo "--- minimap2 索引 $(date '+%T') ---"
if [ ! -s "${NEW}.mmi" ]; then
  minimap2 -x sr -d "${NEW}.mmi.tmp" "$NEW" 2>&1 | tail -2 && mv "${NEW}.mmi.tmp" "${NEW}.mmi"
else
  echo "已存在，跳过"
fi

echo
echo "--- 自检：索引前缀是否等于 FASTA 全名 ---"
for e in amb ann bwt pac sa; do
  [ -s "${NEW}.${e}" ] && echo "  ✅ ${NEW##*/}.${e}" || echo "  ✗ 缺 ${NEW##*/}.${e}"
done
[ -s "${NEW}.mmi" ] && echo "  ✅ ${NEW##*/}.mmi" || echo "  ✗ 缺 .mmi"

echo
echo "--- 产物 ---"
ls -l "$REFDIR" | grep -E 'ref_chr|chr_list'
df -h /home | tail -1
echo "=== end $(date '+%F %T') ==="
