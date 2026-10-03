#!/bin/bash
# 探测 NCBI sra-tools 真实 FTP 下载路径
echo "=== 探测 NCBI FTP sra 目录 ==="
for p in \
  "https://ftp.ncbi.nlm.nih.gov/ncbi-sra/sra-toolkit/" \
  "https://ftp.ncbi.nlm.nih.gov/ncbi-sra/" \
  "https://ftp.ncbi.nlm.nih.gov/genomics/sra/" ; do
  echo "--- $p ---"
  curl -sL --max-time 20 -A "Mozilla/5.0" "$p" 2>&1 | grep -oE 'href="[^"]*"' | grep -iE 'sra|toolkit|ubuntu|linux' | head -15
done
