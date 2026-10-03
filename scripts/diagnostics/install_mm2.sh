#!/usr/bin/env bash
set -u
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
eval "$(/mnt/c/SF_data/tools/micromamba shell hook -s bash)"
micromamba create -y -p /mnt/c/SF_data/tools/mamba/envs/sfru mm2_flag 2>/dev/null || true
micromamba install -y -n sfru -c bioconda -c conda-forge minimap2 samtools 2>&1 | tail -5
micromamba activate sfru
echo "=== 版本 ==="
minimap2 --version 2>&1
samtools --version 2>&1 | head -1
