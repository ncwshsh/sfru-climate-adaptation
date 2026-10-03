#!/bin/bash
# 单 run 测试: SRR31304341 (山西, ~3.3Gb), 经代理
export http_proxy="http://127.0.0.1:7897" https_proxy="http://127.0.0.1:7897"
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy" no_proxy="localhost,127.0.0.1"
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
export MAMBA_ENVS_DIR=/mnt/c/SF_data/tools/mamba/envs
OUT=/mnt/c/SF_data/01_raw; mkdir -p "$OUT"; cd "$OUT"
echo "=== fasterq-dump SRR31304341 (limit 限 5M reads 先测连通) ==="
timeout 300 $MM run -n sra fasterq-dump --split-3 -s 5000000 -O "$OUT" SRR31304341 2>&1 | tail -20
echo "exit=$?"
echo "=== 落盘 ==="
ls -lh "$OUT"/*.fastq.gz 2>/dev/null || echo "(无)"
