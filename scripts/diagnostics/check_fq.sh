#!/usr/bin/env bash
# check_fq.sh —— FASTQ 完整性检查（read ID 是否连续 / 长度是否一致 / 有无非法字符）
# 「截断下载 + 修复」若在文件内部造成字节损坏，read 会错位 -> 高比对率但高错配
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

chk() {
  local f="$1" tag="$2"
  echo "=============================================="
  echo "[$tag]"
  echo "文件: $f   大小: $(stat -c%s "$f" 2>/dev/null) B"
  pigz -dc "$f" 2>/dev/null | awk '
    NR%4==1 {
      n++; id=$1
      num=id; sub(/^@/,"",num); sub(/^[^.]*\./,"",num)
      sub(/[^0-9].*$/,"",num)
      if (num=="") num=-1
      if (n>1 && !gap && num != prevnum+1) { printf "  >> ID 首个断裂点: 第 %d 条  %s -> %s\n", n, previd, id; gap=1; gapline=n }
      prevnum=num; previd=id
      if (id !~ /^@[A-Za-z0-9_.\/:-]+$/) badh++
    }
    NR%4==2 { L=length($0); len[L]++; if ($0 ~ /[^ACGTNacgtn]/) badseq++; lastL=L }
    NR%4==0 { if (length($0) != lastL) badqual++ }
    END {
      printf "  reads = %d   行数 %% 4 = %d\n", n, NR%4
      printf "  序列长度分布: "
      for (k in len) printf "%s bp=%d(%.1f%%) ", k, len[k], 100*len[k]/n
      printf "\n  含非法字符的序列行 = %d (%.4f%%)\n", badseq+0, 100*badseq/n
      printf "  序列/质量长度不一致 = %d\n", badqual+0
      printf "  头部格式异常 = %d\n", badh+0
    }'
  echo
}

chk /mnt/c/SF_data/01_raw/SRR31304341_1.fastq.gz "对照A · 完整下载 · 山西 R1"
chk /home/hugo/data/01_raw/SRR10980085_1.fastq.gz  "实验B · 截断+修复 · 波多黎各 R1"
