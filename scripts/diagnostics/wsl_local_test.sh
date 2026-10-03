#!/bin/bash
# WSL2 localhostForwarding: WSL 里 127.0.0.1 转发到宿主 127.0.0.1
export http_proxy="http://127.0.0.1:7897" https_proxy="http://127.0.0.1:7897" HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy"
echo "=== WSL 127.0.0.1:7897 (localhostForwarding) ==="
for host in ftp.sra.ncbi.nlm.nih.gov sra-pub-run-1.s3.amazonaws.com www.ncbi.nlm.nih.gov; do
  code=$(timeout 20 curl -sI -o /dev/null -w "%{http_code}" "https://$host" 2>/dev/null)
  echo "  $host -> $code"
done
echo "DONE"
