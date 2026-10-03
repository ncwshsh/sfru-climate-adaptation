#!/bin/bash
# 下载 6 代表样本 FASTQ — 经 WSL 127.0.0.1:7897 代理(localhostForwarding)
set -e
# 代理: WSL2 localhostForwarding -> 宿主 127.0.0.1:7897
export http_proxy="http://127.0.0.1:7897" https_proxy="http://127.0.0.1:7897"
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy"
export no_proxy="localhost,127.0.0.1"
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
export MAMBA_ENVS_DIR=/mnt/c/SF_data/tools/mamba/envs
OUT=/mnt/c/SF_data/01_raw
mkdir -p "$OUT"; cd "$OUT"

# 6 个 run: 非洲2(下采样20M reads) + 中国4(小,全量)
declare -A RUNS=(
  [SRR34858431]=20000000
  [SRR34858435]=20000000
  [SRR31304342]=0
  [SRR31304347]=0
  [SRR31304341]=0
  [SRR31304345]=0
)

for srr in SRR34858431 SRR34858435 SRR31304342 SRR31304347 SRR31304341 SRR31304345; do
  limit=${RUNS[$srr]}
  echo "=== $srr limit=$limit ==="
  if [ "$limit" -gt 0 ]; then
    $MM run -n sra fasterq-dump --split-3 -s "$limit" -O "$OUT" "$srr" 2>&1 | tail -4
  else
    $MM run -n sra fasterq-dump --split-3 -O "$OUT" "$srr" 2>&1 | tail -4
  fi
  echo "exit=$?"
done
echo "=== 落盘 ==="
ls -lh "$OUT"/*.fastq.gz 2>/dev/null || echo "(无 fastq)"
echo "DONE"
