#!/usr/bin/env bash
# mergecheck.sh —— 判断两个 BAM 是否为同一文库（reads 是否重复）
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
A=/home/hugo/data/03_align/SRR11528381.dedup.bam
B=/home/hugo/data/03_align/SRR11528382.dedup.bam
T=/home/hugo/data/tmp

echo "===== 1. 前置：磁盘文件是否为 ENA 文件前缀 ====="
FIN=/mnt/c/SF_data/01_raw/SRR11528381_1.fastq.gz
PAR=/mnt/c/SF_data/01_raw/SRR11528381_1.fastq.gz.partial17
echo "  final  = $(stat -c %s "$FIN") B"
echo "  partial= $(stat -c %s "$PAR") B"
if cmp -s -n "$(stat -c %s "$PAR")" "$FIN" "$PAR"; then
  echo "  ✅ final 的前 855638016 B 与 .partial17 完全一致 -> final 是同一前缀的延伸"
else
  echo "  ❌ 前 855638016 B 不一致 -> final 不是 .partial17 的延伸"
fi

echo
echo "===== 2. 读序重叠测试（同文库会大量重复）====="
samtools view "$A" 2>/dev/null | head -300000 | cut -f10 | sort -u > $T/seqA.txt
samtools view "$B" 2>/dev/null | head -300000 | cut -f10 | sort -u > $T/seqB.txt
NA=$(wc -l < $T/seqA.txt); NB=$(wc -l < $T/seqB.txt)
COM=$(comm -12 $T/seqA.txt $T/seqB.txt | wc -l)
echo "  A 唯一序列 = $NA"
echo "  B 唯一序列 = $NB"
echo "  交集       = $COM"
awk -v c="$COM" -v a="$NA" -v b="$NB" 'BEGIN{
  if(a>0&&b>0) printf "  交集占 A 的 %.2f%%  占 B 的 %.2f%%\n", 100*c/a, 100*c/b;
  print (c/((a<b?a:b)+1e-9) > 0.5) ? "  >>> 高度重叠：很可能同一文库，合并几乎没有增益" : "  >>> 重叠很低：两条 lane 基本独立，合并可叠加深度"
}'

echo
echo "===== 3. 各自标记的重复率（markdup 结果）====="
for b in "$A" "$B"; do
  echo "  $(basename $b):"
  samtools flagstat "$b" 2>/dev/null | grep -E "duplicates|mapped \(" | sed 's/^/    /'
done

echo
echo "===== 4. 读名前缀（看 run/flowcell）====="
echo "  A: $(samtools view "$A" 2>/dev/null | head -1 | cut -f1)"
echo "  B: $(samtools view "$B" 2>/dev/null | head -1 | cut -f1)"
