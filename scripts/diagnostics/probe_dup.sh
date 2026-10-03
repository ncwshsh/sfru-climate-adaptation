#!/usr/bin/env bash
# 诊断 SRR10980085 重复率异常 + 核对 Kenya 输入口径
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
A=/home/hugo/data/03_align

echo "########## 1. BAM 标签检查 ##########"
for s in SRR10980085 SRR11528382; do
  echo "--- $s ---"
  samtools view $A/$s.dedup.bam 2>/dev/null | head -1 | awk '{for(i=12;i<=NF;i++) if($i ~ /^(ms|MC|MQ|NM):/) printf "%s ", $i; print ""}'
done

echo
echo "########## 2. 若存在 pre-dedup BAM，比对其重复标记 ##########"
for s in SRR10980085 SRR11528382; do
  for cand in $A/$s.bam /home/hugo/data/tmp/$s.bam; do
    if [ -s "$cand" ]; then
      tot=$(samtools view -c "$cand" 2>/dev/null)
      dup=$(samtools view -c -f 1024 "$cand" 2>/dev/null)
      printf "%-50s total=%-12s dup=%-12s rate=%.3f%%\n" "$cand" "$tot" "$dup" "$(awk -v d="$dup" -v t="$tot" 'BEGIN{if(t>0)print 100*d/t; else print 0}')"
    fi
  done
done

echo
echo "########## 3. 原始 FASTQ 记录数（前 400 万行抽样）##########"
for s in SRR10980085 SRR11528382; do
  for f in /home/hugo/data/01_raw/${s}_1.fastq.gz /home/hugo/data/01_raw/${s}*.fastq.gz; do
    [ -s "$f" ] || continue
    n=$(zcat "$f" 2>/dev/null | head -4000000 | wc -l)
    printf "%-60s 前400万行 -> %s reads(估)\n" "$f" "$((n/4))"
    break
  done
done

echo
echo "########## 4. 已下载输入文件清单（01_raw）##########"
ls -la /home/hugo/data/01_raw/ | awk '{print $5"\t"$9}'

echo
echo "########## 5. 实测可用深度（usable）遗留结果 ##########"
ls -la /home/hugo/data/04_variant/*.txt /home/hugo/data/04_variant/*.log 2>/dev/null | awk '{print $5"\t"$9}'
