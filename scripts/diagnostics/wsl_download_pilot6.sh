#!/bin/bash
# 下载 6 代表样本 FASTQ (fasterq-dump), 限覆盖到 ~10x 以省空间
# 基因组 384Mb. 10x ~ 3.84Gb raw = ~19M 双端 reads/run (若双端)
# SRP268365 ~16Gb -> 下采样; SRP544390 ~3.4Gb -> 基本全量(已<10x 则全量)
set -e
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
export MAMBA_ENVS_DIR=/mnt/c/SF_data/tools/mamba/envs
OUT=/mnt/c/SF_data/01_raw
mkdir -p "$OUT"
cd "$OUT"

# 每个 run 限 20M reads (双端 ~ 20M*2*150bp ~ 6Gb raw ~ 10x); SRP544390 较小全量
# 用 -s 0 表示按 spots 数; 这里用 --clip 不截, 直接限 reads
declare -A RUNS=(
  [SRR34858431]=20000000  # Ghana
  [SRR34858435]=20000000  # Zambia
  [SRR31304342]=0          # Guizhou (小, 全量)
  [SRR31304347]=0          # Yunnan (小, 全量)
  [SRR31304341]=0          # Shanxi (小, 全量)
  [SRR31304345]=0          # Sichuan (小, 全量)
)

for srr in "${!RUNS[@]}"; do
  limit=${RUNS[$srr]}
  echo "=== $srr limit=$limit ==="
  if [ "$limit" -gt 0 ]; then
    $MM run -n sra fasterq-dump --split-3 --max-size 0 -s "$limit" -O "$OUT" "$srr" 2>&1 | tail -3
  else
    $MM run -n sra fasterq-dump --split-3 --max-size 0 -O "$OUT" "$srr" 2>&1 | tail -3
  fi
done
echo "=== 落盘检查 ==="
ls -lh "$OUT"/*.fastq.gz 2>/dev/null || ls -lh "$OUT"
echo "DONE"
