#!/usr/bin/env bash
# fixup_rg.sh —— 补齐缺失的 @RG 头，使 VCF 里样本名正常显示
# 原因：SRR31304341.bam 由上一会话的旧命令生成，未带 RG -> bcftools 用文件路径当样本名
set -u
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
eval "$(/mnt/c/SF_data/tools/micromamba shell hook -s bash)"
micromamba activate sfru

ALN=/mnt/c/SF_data/03_align
mkdir -p /mnt/c/SF_data/tmp

for s in SRR31304341; do
  for kind in "" ".dedup"; do
    src="${ALN}/${s}${kind}.bam"
    [ -f "$src" ] || continue
    if samtools view -H "$src" | grep -q '^@RG'; then
      echo "[skip] $(basename $src) 已有 @RG"
      continue
    fi
    echo "[fix ] $(basename $src) -> 补 @RG"
    samtools addreplacerg -@ 4 \
      -r "ID:${s}" -r "SM:${s}" -r "PL:ILLUMINA" -r "LB:${s}" -r "PU:unit1" \
      -o "${src}.rg.bam" "$src" \
      && mv "${src}.rg.bam" "$src" \
      && samtools index -@ 4 "$src"
    samtools view -H "$src" | grep '^@RG'
  done
done
echo "=== RG 修复完成 ==="
