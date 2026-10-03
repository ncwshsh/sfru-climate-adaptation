#!/usr/bin/env bash
# 用 micromamba 在 WSL 原生文件系统建 sfru 环境（无需 root）
set -x
export MAMBA_ROOT_PREFIX=/home/hugo/mamba
mkdir -p "$MAMBA_ROOT_PREFIX"

eval "$(/mnt/c/SF_data/tools/micromamba shell hook -s bash)"

# 一次装齐，避免上次 "create 空 env + 假包名" 的坑
micromamba create -y \
  -p /home/hugo/mamba/envs/sfru \
  -c conda-forge -c bioconda \
  bwa samtools bcftools minimap2 2>&1 | tail -30

micromamba activate /home/hugo/mamba/envs/sfru

echo "=== 版本确认 ==="
for c in bwa samtools bcftools minimap2; do
  printf "%-10s %s\n" "$c" "$(command -v $c || echo MISSING)"
done
samtools --version 2>&1 | head -1
bcftools --version 2>&1 | head -1
bwa 2>&1 | grep -i version | head -1
minimap2 --version 2>&1
