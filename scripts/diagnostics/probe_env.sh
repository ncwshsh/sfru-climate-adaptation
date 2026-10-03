#!/usr/bin/env bash
echo "=== HOST: $(hostname) / $(cat /etc/os-release 2>/dev/null | grep PRETTY | cut -d= -f2) ==="
echo "=== env 候选 ==="
for p in /root/micromamba/envs /root/miniforge3/envs /home/*/micromamba/envs /home/*/miniforge3/envs /home/*/mambaforge/envs /mnt/c/SF_data/tools/mamba/envs; do
  if [ -d "$p" ]; then echo "FOUND $p"; ls "$p"; fi
done
echo "=== which ==="
for c in bwa samtools bcftools minimap2 micromamba conda; do
  echo "$c => $(command -v $c 2>/dev/null || echo MISSING)"
done
echo "=== 直接列 /home ==="
ls /home 2>/dev/null
echo "=== 找 bwa (2层) ==="
ls /home/*/micromamba/envs/*/bin/bwa /home/*/miniforge3/envs/*/bin/bwa /root/*/envs/*/bin/bwa 2>/dev/null
