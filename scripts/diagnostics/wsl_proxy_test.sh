#!/bin/bash
# 用宿主机 IP 192.168.1.4:7897 代理测 SRA
export http_proxy="http://192.168.1.4:7897" https_proxy="http://192.168.1.4:7897" HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy"
echo "=== 经宿主代理 192.168.1.4:7897 ==="
for host in ftp.sra.ncbi.nlm.nih.gov sra-pub-run-1.s3.amazonaws.com www.ncbi.nlm.nih.gov; do
  code=$(timeout 20 curl -sI -o /dev/null -w "%{http_code}" "https://$host" 2>/dev/null)
  echo "  $host -> $code"
done
echo "DONE"
