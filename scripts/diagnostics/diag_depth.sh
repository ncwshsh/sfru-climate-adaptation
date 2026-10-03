#!/usr/bin/env bash
# diag_depth.sh —— 排查覆盖深度异常 + 修正样本名（WSL 内运行）
set -u
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
eval "$("$MM" shell hook -s bash)"
micromamba activate sfru

ALN=/mnt/c/SF_data/03_align
REF=${ALN}/ref_GCF_023101765.2.fna

echo "########## 1. BAM 里的 SM 标签（样本名来源）##########"
for b in ${ALN}/*.dedup.bam; do
  echo "  $(basename $b):"
  samtools view -H "$b" | grep -m2 "^@RG" | sed 's/^/    /'
done

echo
echo "########## 2. 参考基因组序列构成 ##########"
awk '{n++; s+=$2; if($2>1000000) big++} END{printf "  共 %d 条序列，合计 %.1f Mb，其中 >1Mb 的有 %d 条\n", n, s/1e6, big}' ${REF}.fai
echo "  最大的 8 条："
sort -k2,2nr ${REF}.fai | head -8 | awk '{printf "    %-16s %8.2f Mb\n", $1, $2/1e6}'

echo
echo "########## 3. 真实覆盖深度（抽 3 号染色体的 2 Mb 区间）##########"
for s in SRR31304341 SRR31304345; do
  b=${ALN}/${s}.dedup.bam
  if [ -f "$b" ]; then
    chr=$(sort -k2,2nr ${REF}.fai | head -3 | tail -1 | cut -f1)
    echo "  ${s} @ ${chr}:2000000-4000000"
    samtools depth -a -r "${chr}:2000000-4000000" "$b" 2>/dev/null | awk '
      {d[NR]=$3; s+=$3}
      END{
        n=NR; asort=d; 
        printf "    平均 %.1fx  中位 %dx  (n=%d 位点)\n", s/n, d[int(n/2)], n
      }' 2>/dev/null || samtools depth -a -r "${chr}:2000000-4000000" "$b" | awk '{s+=$3; n++; if($3>mx)mx=$3} END{printf "    平均 %.1fx  最大 %dx  (n=%d)\n", s/n, mx, n}'
  fi
done

echo
echo "########## 4. flagstat 对比（去重前后）##########"
for s in SRR31304341 SRR31304345; do
  for f in ${ALN}/${s}.bam ${ALN}/${s}.dedup.bam; do
    [ -f "$f" ] && echo "  $(basename $f): $(grep -m1 'mapped (' <(samtools flagstat $f))"
  done
done

echo
echo "########## 5. 原始 VCF 的 QUAL 分布（判断是否全是低质量假阳性）##########"
V=/mnt/c/SF_data/04_variant/pilot_0915_raw.vcf.gz
bcftools query -f '%QUAL\n' "$V" 2>/dev/null | awk '
  {q[NR]=$1; s+=$1}
  END{
    n=NR
    printf "  位点总数 %d\n  平均 QUAL %.1f\n  中位 QUAL %.1f\n  QUAL>10 的 %d 个\n  QUAL>30 的 %d 个\n  QUAL>100 的 %d 个\n",
    n, s/n, q[int(n/2)], 0, 0, 0
  }'
bcftools query -f '%QUAL\n' "$V" 2>/dev/null | awk '{if($1>10)a++; if($1>30)b++; if($1>100)c++} END{printf "  QUAL>10: %d\n  QUAL>30: %d\n  QUAL>100: %d\n", a,b,c}'
