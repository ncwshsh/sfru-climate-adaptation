#!/usr/bin/env bash
# copy_one.sh <SRR_N>   —— 把单个 FASTQ 搬到 WSL 原生盘
set -u
s="$1"
SRC=/mnt/c/SF_data/01_raw
DST=/home/hugo/data/01_raw
src="${SRC}/${s}.fastq.gz"
dst="${DST}/${s}.fastq.gz"

if [ -s "$dst" ]; then echo "SKIP $s"; exit 0; fi
if [ ! -s "$src" ]; then echo "MISS $s"; exit 1; fi

if cp "$src" "${dst}.tmp"; then
  mv "${dst}.tmp" "$dst"
  echo "OK $s $(stat -c%s "$dst")"
else
  rm -f "${dst}.tmp"
  echo "FAIL $s"
  exit 1
fi
