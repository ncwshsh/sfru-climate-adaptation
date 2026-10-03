#!/usr/bin/env bash
# smoke_call.sh —— 快速验证 mpileup/call 参数是否正确 + 粗看 Ts/Tv
# 只取 2 Mb 区域，几分钟出结果，避免全量跑 1 小时才发现参数错
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

R=/home/hugo/data/ref/ref_GCF_023101765.2.fna
TMPD=/home/hugo/data/tmp
mkdir -p "$TMPD"

RGN=$(head -1 "${R}.fai" | cut -f1)
echo "region = ${RGN}:1-2000000"
echo "bams   = $(wc -l < /home/hugo/data/bam5.txt) 个"

start=$(date +%s)
bcftools mpileup -f "$R" -a AD,DP -q 20 -Q 20 -d 500 \
  -r "${RGN}:1-2000000" -Ou $(cat /home/hugo/data/bam5.txt) 2>/tmp/mm.err \
  | bcftools call -m -v -a GQ -Oz -o "${TMPD}/smoke.vcf.gz"
rc=$?
end=$(date +%s)
echo "pipeline exit = $rc   耗时 $((end-start)) 秒"

echo "--- mpileup stderr (tail) ---"
tail -5 /tmp/mm.err

echo "--- 产出 ---"
ls -la "${TMPD}/smoke.vcf.gz" 2>/dev/null || echo "(无产出)"

echo "--- 统计 ---"
bcftools index -t "${TMPD}/smoke.vcf.gz" 2>/dev/null
bcftools stats -F "$R" "${TMPD}/smoke.vcf.gz" 2>/dev/null | grep -E "^SN|Ts/Tv"

echo "--- 基因型构成 ---"
bcftools query -f '[%GT ]\n' "${TMPD}/smoke.vcf.gz" 2>/dev/null \
  | tr ' ' '\n' | grep -v '^$' | sort | uniq -c | sort -rn | head -6
