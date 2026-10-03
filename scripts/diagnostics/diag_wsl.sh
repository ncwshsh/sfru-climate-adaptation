#!/usr/bin/env bash
# diag_wsl.sh —— WSL 环境体检（在 WSL 内执行）
echo "===== 发行版 ====="
. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME"
echo "内核: $(uname -r)"
echo "CPU : $(nproc) 核"
free -h | awk 'NR==2{print "内存: "$2" 总量 / "$7" 可用"}'
df -h /mnt/c 2>/dev/null | awk 'NR==2{print "C盘 : "$4" 可用"}'
df -h /       2>/dev/null | awk 'NR==2{print "WSL盘: "$4" 可用"}'

echo
echo "===== 数据盘挂载 ====="
for p in 00_ref 01_raw 02_qc 03_align 04_variant tools; do
  n=$(ls /mnt/c/SF_data/$p 2>/dev/null | wc -l)
  echo "  /mnt/c/SF_data/$p : $n 项"
done

echo
echo "===== 分析栈 ====="
MM=/mnt/c/SF_data/tools/micromamba
if [ -x "$MM" ]; then
  echo "micromamba: OK ($(stat -c %s "$MM") 字节)"
  export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
  eval "$("$MM" shell hook -s bash)" 2>/dev/null
  micromamba activate sfru 2>/dev/null
  echo "已激活环境: ${CONDA_PREFIX:-<未激活>}"
  for t in bwa samtools bcftools fastqc bgzip tabix; do
    if command -v $t >/dev/null 2>&1; then
      printf "  ✅ %-10s %s\n" "$t" "$($t 2>&1 | head -2 | tr '\n' ' ' | cut -c1-60)"
    else
      printf "  ❌ %-10s MISSING\n" "$t"
    fi
  done
else
  echo "micromamba: ❌ 不存在或不可执行 ($MM)"
fi

echo
echo "===== 参考基因组与索引 ====="
ls -lh /mnt/c/SF_data/03_align/ref.amb /mnt/c/SF_data/03_align/ref.sa \
       /mnt/c/SF_data/03_align/ref_GCF_023101765.2.fna.fai 2>/dev/null
