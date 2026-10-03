#!/bin/bash
set -e
cd /tmp
echo "=== 下载 sra-tools 3.4.1 (ubuntu2204) ==="
# NCBI 官方 GitHub release 资产名规律: sratoolkit.ubuntu2204.x86_64.tar.gz
VER=3.4.1
for url in \
  "https://github.com/ncbi/sra-tools/releases/download/${VER}/sratoolkit.${VER}.ubuntu2204.x86_64.tar.gz" \
  "https://github.com/ncbi/sra-tools/releases/download/${VER}/sratoolkit.${VER}.linux.x86_64.tar.gz" \
  "https://ftp.ncbi.nlm.nih.gov/ncbi-sra/sra-toolkit/sratoolkit.${VER}.ubuntu2204.x86_64.tar.gz" ; do
  echo "try: $url"
  if curl -sL --max-time 180 -A "Mozilla/5.0" -o /tmp/sra.tar.gz "$url" && [ -s /tmp/sra.tar.gz ]; then
    sz=$(du -h /tmp/sra.tar.gz | cut -f1)
    echo "OK downloaded $sz"
    # 校验是 tar.gz
    if tar -tzf /tmp/sra.tar.gz >/dev/null 2>&1; then
      echo "tar.gz valid"
      break
    else
      echo "not a valid tar.gz, try next"
      rm -f /tmp/sra.tar.gz
    fi
  else
    echo "download failed, try next"
    rm -f /tmp/sra.tar.gz
  fi
done
if [ ! -s /tmp/sra.tar.gz ]; then
  echo "ALL SOURCES FAILED"
  # 列出 release 页面找真实资产名
  echo "=== releases page assets ==="
  curl -sL --max-time 30 -A "Mozilla/5.0" "https://github.com/ncbi/sra-tools/releases" | grep -oE 'releases/download/[^"]+\.tar\.gz' | sort -u | head
  exit 1
fi
echo "=== 解压到 /usr/local ==="
tar -xzf /tmp/sra.tar.gz -C /tmp
# 找到包含 bin 的目录
SRC=$(find /tmp -maxdepth 2 -name "fasterq-dump" -type f 2>/dev/null | head -1)
if [ -z "$SRC" ]; then
  echo "fasterq-dump not found in extracted tree, listing:"
  find /tmp -maxdepth 2 -name "*sra*" -o -maxdepth 2 -name "bin" 2>/dev/null | head
  exit 1
fi
BINDIR=$(dirname "$SRC")
echo "bin dir: $BINDIR"
cp -r "$BINDIR/." /usr/local/bin/ 2>/dev/null || sudo cp -r "$BINDIR/." /usr/local/bin/
echo "=== 验证 ==="
export PATH=/usr/local/bin:$PATH
fasterq-dump --version 2>&1 | head -2 || echo "version check failed"
which fasterq-dump
echo "DONE"
