#!/usr/bin/env bash
# 用 apt 安装比对/变异检测工具链 (Ubuntu 24.04 源版本足够)
set -x
echo "=== whoami: $(whoami) ==="
sudo -n true 2>&1 && echo "SUDO_OK" || echo "SUDO_NEED_PW"

export DEBIAN_FRONTEND=noninteractive
sudo -n apt-get update -qq 2>&1 | tail -3
sudo -n apt-get install -y -qq bwa samtools bcftools minimap2 2>&1 | tail -15

echo "=== 版本确认 ==="
for c in bwa samtools bcftools minimap2; do
  printf "%-10s %s\n" "$c" "$(command -v $c || echo MISSING)"
done
bwa 2>&1 | head -3
samtools --version 2>&1 | head -1
bcftools --version 2>&1 | head -1
minimap2 --version 2>&1
