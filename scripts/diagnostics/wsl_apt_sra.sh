#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
echo "=== apt update ==="
apt-get update -qq 2>&1 | tail -3
echo "=== 安装 sra-tools (Ubuntu 官方源) ==="
apt-get install -y sra-tools 2>&1 | tail -15
echo "=== 验证 ==="
export PATH=$PATH:/usr/bin
which fasterq-dump && fasterq-dump --version 2>&1 | head -2 || echo "fasterq-dump NOT available"
echo "DONE"
