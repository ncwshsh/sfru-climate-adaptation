#!/bin/bash
# fasterq-dump 强制 S3, 经代理. 设 VDB 日志看它到底连哪
export http_proxy="http://127.0.0.1:7897" https_proxy="http://127.0.0.1:7897"
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy" no_proxy="localhost,127.0.0.1"
# 强制 S3 + 跳过 ftp.sra 元数据探测
export VDB_DISABLE_S3=0
export AWS_EC2_METADATA_DISABLED=true
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
export MAMBA_ENVS_DIR=/mnt/c/SF_data/tools/mamba/envs
cd /mnt/c/SF_data/01_raw

echo "=== 试1: --s3 + -a (alt server s3) ==="
timeout 180 $MM run -n sra fasterq-dump --s3 --split-3 -s 3000000 -O /mnt/c/SF_data/01_raw SRR31304341 2>&1 | tail -8

echo "=== 试2: 用 sra-dump 看 run 元数据(定位它连的host) ==="
export SRATOOLS_LOG_LEVEL=5
timeout 60 $MM run -n sra vdb-dump --version 2>&1 | head -1
# 直接看 fasterq-dump 的 verbose 网络日志
timeout 120 env SRATOOLS_LOG_LEVEL=5 $MM run -n sra fasterq-dump --s3 -s 1000000 -O /mnt/c/SF_data/01_raw SRR31304341 2>&1 | grep -iE 'connect|ref|s3|sra|http|ncbi|endpoint|resolve|fail|error|timeout' | head -30
ls -lh /mnt/c/SF_data/01_raw/*.fastq.gz 2>/dev/null || echo "(无 fastq)"
echo "DONE"
