#!/bin/bash
export http_proxy="http://127.0.0.1:7897" https_proxy="http://127.0.0.1:7897"
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy" no_proxy="localhost,127.0.0.1"
export SRATOOLS_LOG_LEVEL=3
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
export MAMBA_ENVS_DIR=/mnt/c/SF_data/tools/mamba/envs
cd /mnt/c/SF_data/01_raw
echo "=== 详细日志 (SRATOOLS_LOG_LEVEL=3) ==="
timeout 120 $MM run -n sra fasterq-dump -O /mnt/c/SF_data/01_raw SRR31304341 2>&1 | grep -iE 'connect|ftp|sra|error|fail|http|timeout|s3|ncbi|ref|external' | head -40
echo "---"
# 也测: 不经代理, 直连 ftp.sra (看是否 DNS 问题)
echo "=== DNS 解析 ftp.sra.ncbi.nlm.nih.gov ==="
getent hosts ftp.sra.ncbi.nlm.nih.gov || echo "DNS fail"
echo "=== 直连(无代理) ftp.sra ==="
env -u http_proxy -u https_proxy timeout 15 curl -sI -o /dev/null -w "%{http_code}\n" "https://ftp.sra.ncbi.nlm.nih.gov/" 2>&1 || echo "direct fail"
