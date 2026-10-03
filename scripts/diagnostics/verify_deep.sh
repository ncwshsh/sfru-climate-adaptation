#!/usr/bin/env bash
# verify_deep.sh —— 校验 60% 版 FASTQ：gzip 流完整性 + 与 30% 版前缀一致 + 抽查 30-60% 新区段对 ENA
export PATH="/usr/bin:/bin:$PATH"
cd /c/SF_data/01_deep || exit 1
PROXY="${PROXY:-http://127.0.0.1:7897}"

echo "=== 1. 文件与字节数 ==="
ls -l SRR12044649_1.fastq.gz.partial60 SRR12044649_2.fastq.gz.partial60 2>/dev/null
for f in SRR12044649_1.fastq.gz.partial60 SRR12044649_2.fastq.gz.partial60; do
  printf '%-40s magic=' "$f"; head -c 4 "$f" | od -An -tx1 | tr -d ' \n'; echo
done

echo
echo "=== 2. gzip 流完整性（只允许 unexpected end of file）==="
for f in SRR12044649_1.fastq.gz.partial60 SRR12044649_2.fastq.gz.partial60; do
  msg=$(gzip -t "$f" 2>&1 | head -2)
  echo "$f -> ${msg:-OK(无错)}"
done

echo
echo "=== 3. 30% 版是否为 60% 版的前缀（应为一致）==="
for m in 1 2; do
  a=SRR12044649_${m}.fastq.gz.partial30
  b=SRR12044649_${m}.fastq.gz.partial60
  [ -s "$a" ] || { echo "mate$m: 无 30% 版，跳过"; continue; }
  sz=$(stat -c %s "$a")
  if cmp -s -n "$sz" "$a" "$b"; then echo "mate$m: ✅ 前 $sz 字节完全一致"; else echo "mate$m: ✗ 前缀不一致"; fi
done

echo
echo "=== 4. 抽查 30-60% 新区段对 ENA 原站 ==="
OFF=3000000000; LEN=16777216
for m in 1 2; do
  case $m in
    1) U="https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR120/049/SRR12044649/SRR12044649_1.fastq.gz";;
    2) U="https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR120/049/SRR12044649/SRR12044649_2.fastq.gz";;
  esac
  tail -c +$((OFF+1)) "SRR12044649_${m}.fastq.gz.partial60" | head -c $LEN > /tmp/_m${m}.bin
  curl -s -x "$PROXY" -r ${OFF}-$((OFF+LEN-1)) "$U" > /tmp/_e${m}.bin
  if cmp -s /tmp/_m${m}.bin /tmp/_e${m}.bin; then
    echo "mate$m: ✅ 新区段 $OFF..$((OFF+LEN-1)) 与 ENA 逐字节一致"
  else
    echo "mate$m: ✗ 新区段不一致"; cmp /tmp/_m${m}.bin /tmp/_e${m}.bin | head -2
  fi
done
rm -f /tmp/_m1.bin /tmp/_m2.bin /tmp/_e1.bin /tmp/_e2.bin

echo
echo "=== 5. FASTQ 结构抽查 ==="
gzip -dc SRR12044649_1.fastq.gz.partial60 2>/dev/null | tail -8
echo "... 行数（头 400 万行）:"
gzip -dc SRR12044649_1.fastq.gz.partial60 2>/dev/null | head -4000000 | awk 'END{print "lines="NR" reads="NR/4}'
