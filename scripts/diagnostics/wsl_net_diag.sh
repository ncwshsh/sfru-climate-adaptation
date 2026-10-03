#!/bin/bash
# 诊断 WSL 内 fasterq-dump 的网络: 找宿主 IP, 测 SRA 服务器可达性
echo "=== WSL 默认网关(宿主) ==="
GW=$(ip route | grep default | awk '{print $3}')
echo "gateway=$GW"
echo "=== 不设代理直连 SRA 服务器 ==="
for host in ftp.sra.ncbi.nlm.nih.gov sra-pub-run-1.s3.amazonaws.com; do
  code=$(timeout 12 curl -sI -o /dev/null -w "%{http_code}" "https://$host" 2>/dev/null)
  echo "  no-proxy  $host -> $code"
done
echo "=== 设代理(宿主:7897)连 SRA ==="
export http_proxy="http://$GW:7897" https_proxy="http://$GW:7897"
for host in ftp.sra.ncbi.nlm.nih.gov sra-pub-run-1.s3.amazonaws.com; do
  code=$(timeout 15 curl -sI -o /dev/null -w "%{http_code}" "https://$host" 2>/dev/null)
  echo "  proxy     $host -> $code"
done
echo "DONE"
