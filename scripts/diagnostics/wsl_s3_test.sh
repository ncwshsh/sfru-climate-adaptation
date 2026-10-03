#!/bin/bash
# fasterq-dump --s3 强制 S3 模式(不连废弃的 ftp.sra)
export http_proxy="http://127.0.0.1:7897" https_proxy="http://127.0.0.1:7897"
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy" no_proxy="localhost,127.0.0.1"
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
export MAMBA_ENVS_DIR=/mnt/c/SF_data/tools/mamba/envs
cd /mnt/c/SF_data/01_raw
echo "=== fasterq-dump --s3 SRR31304341 (限5M reads 测试) ==="
timeout 240 $MM run -n sra fasterq-dump --s3 --split-3 -s 5000000 -O /mnt/c/SF_data/01_raw SRR31304341 2>&1 | tail -20
echo "exit=$?"
ls -lh /mnt/c/SF_data/01_raw/*.fastq.gz 2>/dev/null || echo "(无 fastq)"
