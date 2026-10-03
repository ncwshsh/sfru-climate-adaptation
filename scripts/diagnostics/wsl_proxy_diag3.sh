#!/bin/bash
# 诊断: WSL 经 127.0.0.1:7897 代理解析 SRA 域名
export http_proxy="http://127.0.0.1:7897" https_proxy="http://127.0.0.1:7897"
echo "=== curl --resolve 对照: 先经代理拿 www.ncbi (已知能通) ==="
code=$(timeout 20 curl -sI -o /dev/null -w "%{http_code}" "https://www.ncbi.nlm.nih.gov/" 2>/dev/null)
echo "  www.ncbi via proxy -> $code"

echo "=== 关键: ftp.sra 经代理 (curl 由代理做DNS) ==="
code=$(timeout 25 curl -sI -o /dev/null -w "%{http_code}|%{remote_ip}" "https://ftp.sra.ncbi.nlm.nih.gov/" 2>/dev/null)
echo "  ftp.sra via proxy -> $code"

echo "=== S3 桶经代理 (拿 remote_ip 确认代理代解析成功) ==="
for b in sra-pub-run-1 sra-pub-run-2 sra-pub-run-16; do
  code=$(timeout 25 curl -sI -o /dev/null -w "%{http_code}|%{remote_ip}" "https://$b.s3.amazonaws.com/" 2>/dev/null)
  echo "  $b via proxy -> $code"
done

echo "=== 代理是否支持 SOCKS/是否全局: 查 7897 端口协议 ==="
timeout 8 bash -c 'echo -e "GET / HTTP/1.0\r\nHost: x\r\n\r\n" | timeout 5 nc 127.0.0.1 7897 2>/dev/null' | head -2 || echo "  (nc 无响应或非HTTP代理)"
echo "DONE"
