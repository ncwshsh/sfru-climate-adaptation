#!/bin/bash
# 用 micromamba 在 WSL2 装 sra-tools (linux-64, conda-forge)
set -e
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
export MAMBA_ENVS_DIR=/mnt/c/SF_data/tools/mamba/envs
MM=/mnt/c/SF_data/tools/micromamba
echo "=== 下载 micromamba ==="
if [ ! -x "$MM" ]; then
  curl -sL --max-time 120 -o /tmp/mamba.tar.bz2 \
    "https://micro.mamba.pm/api/micromamba/linux-64/latest"
  tar -xjf /tmp/mamba.tar.bz2 -C /tmp bin/micromamba
  cp /tmp/bin/micromamba "$MM"
  chmod +x "$MM"
fi
"$MM" --version
echo "=== 创建 env 并装 sra-tools ==="
$MM create -y -n sra -c conda-forge sra-tools 2>&1 | tail -25
echo "=== 验证 fasterq-dump ==="
$MM run -n sra which fasterq-dump
$MM run -n sra fasterq-dump --version 2>&1 | head -3
echo "DONE"
