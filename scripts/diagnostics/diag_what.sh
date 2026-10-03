#!/usr/bin/env bash
# diag_what.sh —— 未比对 reads 的性质：重复度 + 高频序列 top10 + kmer 复杂度
# 判读：
#   unique 比例极低 + top 序列占比高 ⇒ 接头二聚体 / PCR 假象（技术，可修）
#   unique 比例高 + 序列像生物序列     ⇒ 外源生物污染或样本标注错误（该剔除）
# 用法（WSL 内）: bash /mnt/c/SF_data/tools/diag_what.sh <BAM前缀>
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
B=/mnt/c/SF_data/03_align
S="$1"
echo "===== $S 未比对 reads 组成 ====="
samtools view -f4 "$B/$S.dedup.bam" 2>/dev/null | head -30000 | awk '
{ s=$10; n=length(s); if(n==0) next
  cnt[s]++; tot++
}
END{
  u=length(cnt)
  printf "  抽样 %d 条，unique 序列 %d 条（%.1f%%）\n", tot, u, u*100/tot
  print "  --- 出现最多的 8 条序列 ---"
  for (s in cnt) print cnt[s]"\t"substr(s,1,66)
}' | sort -rn | head -12
