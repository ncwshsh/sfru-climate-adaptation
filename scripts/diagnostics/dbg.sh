#!/bin/bash
export PATH=/home/hugo/mamba/envs/sfru/bin:/usr/bin:/bin
REF=/home/hugo/data/ref/ref_GCF_023101765.2.fna
A=/home/hugo/data/03_align/SRR11528381.dedup.bam
B=/home/hugo/data/03_align/SRR12044628.dedup.bam
REG=NC_064212.1:1-20000

echo "===== 原始 mpileup 前 10 行 ====="
samtools mpileup -f "$REF" -r "$REG" -q 30 -Q 20 -d 2000 "$A" "$B" 2>/dev/null | head -10

echo
echo "===== 字段数分布 ====="
samtools mpileup -f "$REF" -r "$REG" -q 30 -Q 20 -d 2000 "$A" "$B" 2>/dev/null | awk '{print NF}' | sort | uniq -c

echo
echo "===== 该 20kb 区段的覆盖情况 ====="
echo "--- A 单独 mpileup 行数 ---"
samtools mpileup -f "$REF" -r "$REG" -q 30 -Q 20 "$A" 2>/dev/null | wc -l
echo "--- A 无 -q 过滤行数 ---"
samtools mpileup -f "$REF" -r "$REG" "$A" 2>/dev/null | wc -l
echo "--- A 的 depth>=5 位点数(无MAPQ过滤) ---"
samtools mpileup -f "$REF" -r "$REG" "$A" 2>/dev/null | awk '$4>=5' | wc -l
echo "--- A 的 depth>=5 位点数(-q 30) ---"
samtools mpileup -f "$REF" -r "$REG" -q 30 -Q 20 "$A" 2>/dev/null | awk '$4>=5' | wc -l
echo "--- 参考在该区段是否有 N ---"
samtools faidx "$REF" "$REG" | grep -v '^>' | tr -d '\n' | tr -cd 'Nn' | wc -c
