#!/usr/bin/env bash
export MAMBA_ROOT_PREFIX=/home/hugo/mamba
eval "$(/mnt/c/SF_data/tools/micromamba shell hook -s bash)"
micromamba install -y -n sfru -c conda-forge pigz 2>&1 | tail -8
echo "=== 确认 ==="
/home/hugo/mamba/envs/sfru/bin/pigz --version 2>&1 | head -2
