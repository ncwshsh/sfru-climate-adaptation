#!/bin/bash
# 一次性对账脚本：S2 队列 220 样本双端齐备检查（只读）
export PATH="/usr/bin:/bin:$PATH"
RAW=/c/SF_data/01_raw
TSV=/c/SF_data/tools/cohort_formal_s2.tsv

ls -la "$RAW" > /tmp/raw_ls.txt

awk '
NR==FNR {
  # 解析 ls -la 输出：$5=size, $9..=name
  name=""; for(i=9;i<=NF;i++) name=(name==""?$i:name" "$i)
  if (name=="" || name=="." || name=="..") next
  size=$5+0; total+=size
  if (name ~ /^\.bad\./) { bad++; next }
  if (name ~ /^\.nrec\./) {
    base=substr(name,7)  # 去掉 .nrec.
    if (match(base, /^(SRR[0-9]+)_([12])\.fastq\.gz/)) {
      run=substr(base,1,RLENGTH-10); mate=substr(base,RLENGTH-9+10,1)
      # 用正则捕 run 与 mate
      r=base; sub(/^\.?nrec\./,"",r)
      split(r,a,"_"); run=a[1]; m=a[2]; sub(/\..*/,"",m); mate=m
      nrec[run,mate]=1
    }
    next
  }
  if (match(name, /^SRR[0-9]+_[12]\.fastq\.gz$/)) {
    split(name,a,"_"); run=a[1]; m=a[2]; sub(/\..*/,"",m)
    final[run,m]=1; next
  }
  if (match(name, /^SRR[0-9]+_[12]\.fastq\.gz\.partial[0-9]+$/)) {
    split(name,a,"_"); run=a[1]; m=a[2]; sub(/\..*/,"",m)
    part[run,m]=1; next
  }
  if (match(name, /^SRR[0-9]+_[12]\.fastq\.gz\.partial[0-9]+\.part[0-9]+$/)) {
    frag++; next
  }
  next
}
FNR==1 { next }  # tsv 表头
{
  run=$1; mod=$3
  n++; nmod[mod]++
  m1 = ((run,1) in final) || ((run,1) in part) || ((run,1) in nrec)
  m2 = ((run,2) in final) || ((run,2) in part) || ((run,2) in nrec)
  if (m1 && m2) { ok++; okmod[mod]++ }
  else {
    miss++
    detail=(!m1&&!m2)?"双端皆缺":(!m1?"缺_1":"缺_2")
    missmod[mod]++
    printf "MISS\t%s\t%s\t%s\n", run, mod, detail
  }
}
END {
  printf "\n===== 汇总 =====\n"
  printf "队列样本数: %d\n", n
  printf "双端齐备:   %d\n", ok
  printf "缺失:       %d\n", miss
  printf "分模块: "
  for (m in nmod) printf "%s %d/%d | ", m, okmod[m]+0, nmod[m]
  printf "\n"
  printf ".bad 隔离文件数: %d\n", bad+0
  printf "进行中分块(.partN)文件数: %d\n", frag+0
  printf "01_raw 总体积: %.1f GB\n", total/1073741824
}' /tmp/raw_ls.txt "$TSV"

echo "===== 磁盘余量 ====="
df -h /c/SF_data | tail -1
