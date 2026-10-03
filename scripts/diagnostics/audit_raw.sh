#!/usr/bin/env bash
# audit_raw.sh —— 只读审计 C:/SF_data/01_raw 的存储构成
export PATH="/usr/bin:/bin:$PATH"
D=/c/SF_data/01_raw
cd "$D" || exit 1

echo "===== 文件总数 ====="
ls -1 | wc -l

echo
echo "===== 按类别统计（个数 / 总字节）====="
ls -l | awk '
  /^total/ {next}
  {
    name=$NF
    sz=$5
    if (name ~ /\.part[0-9]+$/)        { c_part++; b_part+=sz }
    else if (name ~ /\.partial[0-9]+$/) { c_pfinal++; b_pfinal+=sz }
    else if (name ~ /\.partial[0-9]+\.part[0-9]+$/) { c_part++; b_part+=sz }
    else if (name ~ /\.fastq\.gz$/)    { c_final++; b_final+=sz }
    else if (name ~ /^\.blocks_/)      { c_blk++; b_blk+=sz }
    else if (name ~ /^\.log_/)         { c_log++; b_log+=sz }
    else                               { c_other++; b_other+=sz; other[name]=sz }
  }
  END{
    printf "  %-26s %7d 个 %12.2f GB\n", "块碎片 .partN",        c_part,   b_part/1e9
    printf "  %-26s %7d 个 %12.2f GB\n", "半成品 .partialN",     c_pfinal, b_pfinal/1e9
    printf "  %-26s %7d 个 %12.2f GB\n", "成品 .fastq.gz",        c_final,  b_final/1e9
    printf "  %-26s %7d 个 %12.2f MB\n", ".blocks_ 清单",        c_blk,    b_blk/1e6
    printf "  %-26s %7d 个 %12.2f MB\n", ".log_ 日志",           c_log,    b_log/1e6
    printf "  %-26s %7d 个 %12.2f GB\n", "其它",                 c_other,  b_other/1e9
    printf "  ---- 合计 %.2f GB ----\n", (b_part+b_pfinal+b_final+b_blk+b_log+b_other)/1e9
    n=0
    for (k in other) { if (n<12) { printf "    [其它样张] %s (%d B)\n", k, other[k]; n++ } }
  }'

echo
echo "===== 涉及多少个不同的 SRR ====="
ls -1 | grep -oE '^SRR[0-9]+|^ERR[0-9]+' | sort -u | wc -l

echo
echo "===== 有成品 .fastq.gz 的样本数（成对=2个文件）====="
ls -1 | grep -E '_fastq\.gz$|\.fastq\.gz$' | grep -vE 'partial|\.part' | sed -E 's/_?[12]\.fastq\.gz$//' | sort -u | wc -l

echo
echo "===== 磁盘 ====="
df -h /c | tail -1
echo
echo "===== 最大的 15 个文件 ====="
ls -lS | head -16 | awk '{printf "  %12d  %s\n", $5, $NF}'
