#!/usr/bin/env bash
# verify_ref.sh —— 用 NCBI 官方 md5 校验参考基因组文件是否损坏
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
cd /tmp || exit 1
URL=https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/023/101/765/GCF_023101765.2_AGI-APGP_CSIRO_Sfru_2.0/md5checksums.txt

echo "=== 拉取官方 md5 ==="
if curl -fsSL --max-time 60 "$URL" -o md5sums.txt; then
  echo "OK，官方 md5 清单："
  cat md5sums.txt
else
  echo "!! 下载失败（可能需要代理）"
fi

echo
echo "=== 本地 gz 文件（C:\\SF_data\\00_ref）实际 md5 ==="
md5sum /mnt/c/SF_data/00_ref/*.gz 2>/dev/null

echo
echo "=== WSL 盘参考 fna（解压后）==="
ls -la /home/hugo/data/ref/
md5sum /home/hugo/data/ref/ref_GCF_023101765.2.fna

echo
echo "=== 序列条数 / 总长 ==="
grep -c '^>' /home/hugo/data/ref/ref_GCF_023101765.2.fna
awk '/^>/{next}{s+=length($0)}END{print "总长 = "s" bp"}' /home/hugo/data/ref/ref_GCF_023101765.2.fna
