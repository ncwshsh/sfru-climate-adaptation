#!/bin/bash
# 分类量化 01_raw / 01_deep 的存储占用
export PATH="/usr/bin:/bin:$PATH"

for D in /c/SF_data/01_raw /c/SF_data/01_deep; do
  echo "############################################################"
  echo "## $D"
  echo "############################################################"

  # 用 find 一次性输出 大小|mtime|文件名，然后 awk 分类聚合
  find "$D" -maxdepth 1 -type f -printf '%s\t%TY-%Tm-%Td %TH:%TM\t%f\n' 2>/dev/null \
  | awk -F'\t' '
  {
    sz=$1; mt=$2; fn=$3;
    # 分类
    if (fn ~ /\.part[0-9]+$/)            {cat="1_orphan_block(.partN)"}
    else if (fn ~ /\.partial[0-9]+\.part[0-9]+$/) {cat="1_orphan_block(.partialN.partM)"}
    else if (fn ~ /\.partial[0-9]+$/)    {cat="2_merged_partial(.partialN)"}
    else if (fn ~ /\.fq\.gz$/ || fn ~ /\.fastq\.gz$/) {cat="3_complete_fastq"}
    else if (fn ~ /\.(bam|bai|vcf|gz\.tbi|log|txt|tsv|csv|fai|amb|ann|bwt|pac|sa|dict)$/) {cat="4_other_known"}
    else                                  {cat="5_UNKNOWN"}
    cnt[cat]++; bytes[cat]+=sz;
    if (mtmin[cat]=="" || mt<mtmin[cat]) mtmin[cat]=mt;
    if (mtmax[cat]=="" || mt>mtmax[cat]) mtmax[cat]=mt;
    if (maxsz[cat]<sz) {maxsz[cat]=sz; maxfn[cat]=fn}
  }
  END{
    printf "%-34s %8s %14s %20s %20s\n","类别","文件数","总大小(GB)","最早mtime","最晚mtime"
    for (c in cnt)
      printf "%-34s %8d %14.2f %20s %20s\n", c, cnt[c], bytes[c]/1073741824, mtmin[c], mtmax[c]
    print ""
    for (c in maxfn) printf "  最大单文件[%s] = %s (%.2f GB)\n", c, maxfn[c], maxsz[c]/1073741824
  }'
  echo
  echo "--- 顶层目录 ---"
  find "$D" -maxdepth 1 -mindepth 1 -type d -printf '%f\n' 2>/dev/null
  echo
done
