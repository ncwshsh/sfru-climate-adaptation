#!/bin/bash
# 免 bzip2：用 python3 解 bz2 装 micromamba
set -e
MM=/mnt/c/SF_data/tools/micromamba
echo "=== 重新下载 micromamba tar.bz2 ==="
curl -sL --max-time 120 -o /tmp/mamba.tar.bz2 \
  "https://micro.mamba.pm/api/micromamba/linux-64/latest"
ls -la /tmp/mamba.tar.bz2
echo "=== 用 python3 解压 bz2 -> tar ==="
python3 -c "import bz2,shutil; d=bz2.open('/tmp/mamba.tar.bz2','rb').read(); open('/tmp/mamba.tar','wb').write(d); print('unbz2 ok', len(d))"
echo "=== tar 解出 bin/micromamba ==="
mkdir -p /tmp/mambaext
tar -xf /tmp/mamba.tar -C /tmp/mambaext
find /tmp/mambaext -name micromamba -type f
cp /tmp/mambaext/bin/micromamba "$MM"
chmod +x "$MM"
"$MM" --version
echo "=== 创建 env 装 sra-tools ==="
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
export MAMBA_ENVS_DIR=/mnt/c/SF_data/tools/mamba/envs
$MM create -y -n sra -c conda-forge sra-tools 2>&1 | tail -30
echo "=== 验证 ==="
$MM run -n sra which fasterq-dump
$MM run -n sra fasterq-dump --version 2>&1 | head -3
echo "DONE"
