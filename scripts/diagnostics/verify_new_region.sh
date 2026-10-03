#!/usr/bin/env bash
# verify_new_region.sh —— 只做一件事：抽查 60% 版在 30–60% 新区段是否与 ENA 原站逐字节一致
export PATH="/usr/bin:/bin:$PATH"
cd /c/SF_data/01_deep || exit 1
PROXY="${PROXY:-http://127.0.0.1:7897}"
OFF=${1:-3000000000}
LEN=8388608

for m in 1 2; do
  case $m in
    1) U="https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR120/049/SRR12044649/SRR12044649_1.fastq.gz";;
    2) U="https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR120/049/SRR12044649/SRR12044649_2.fastq.gz";;
  esac
  F="SRR12044649_${m}.fastq.gz.partial60"
  echo "[$(date '+%T')] mate$m offset=$OFF 取本地片段..."
  tail -c +$((OFF+1)) "$F" | head -c $LEN > "/tmp/_m${m}.bin"
  echo "[$(date '+%T')] mate$m 从 ENA 拉同区段..."
  curl -s --max-time 300 -x "$PROXY" -r ${OFF}-$((OFF+LEN-1)) "$U" > "/tmp/_e${m}.bin"
  lm=$(stat -c %s "/tmp/_m${m}.bin"); le=$(stat -c %s "/tmp/_e${m}.bin")
  echo "       本地=$lm  ENA=$le"
  if [ "$lm" = "$LEN" ] && [ "$le" = "$LEN" ] && cmp -s "/tmp/_m${m}.bin" "/tmp/_e${m}.bin"; then
    echo "       ✅ mate$m 新区段 $OFF..$((OFF+LEN-1)) 逐字节一致"
  else
    echo "       ✗ mate$m 不一致或长度不足"
    cmp "/tmp/_m${m}.bin" "/tmp/_e${m}.bin" 2>&1 | head -2
  fi
  rm -f "/tmp/_m${m}.bin" "/tmp/_e${m}.bin"
done
echo "[$(date '+%T')] 完成"
