#!/usr/bin/env bash
# test_trim.sh —— 端到端验证 dl_ena.sh 的 4b 裁尾代码路径
# 造一个「截断在记录中间」的 gzip，跑与 dl_ena.sh 完全相同的流水线，检查产物是否完整
export PATH=/usr/bin:/bin:$PATH
T=/tmp/trimtest
rm -rf "$T"; mkdir -p "$T"
SRR=TESTRUN; mate=1; PCT=30; TRIM=1

# 1) 造 20000 条记录的 FASTQ，压成 gzip
awk 'BEGIN{for(i=1;i<=20000;i++){s="";q="";for(j=1;j<=151;j++){s=s substr("ACGT",int(rand()*4)+1,1); q=q"I"}; printf "@TESTRUN.%d %d/1\n%s\n+\n%s\n", i, i, s, q}}' > "$T/orig.fq"
gzip -c "$T/orig.fq" > "$T/full.fq.gz"
fullsz=$(stat -c%s "$T/full.fq.gz")
# 2) 切到一个必然落在记录中间的字节数（取完整大小的 61%，再偏移 137 字节）
cut=$(( fullsz * 61 / 100 + 137 ))
head -c "$cut" "$T/full.fq.gz" > "$T/trunc.fq.gz"
echo "完整 gzip = $fullsz B ；截断到 $cut B"
echo "--- 截断文件解压后末尾 4 行（应看见半条记录）---"
gzip -dc "$T/trunc.fq.gz" 2>/dev/null | tail -4 | awk '{printf "  len=%-4d %s\n", length($0), substr($0,1,50)}'

# 3) 原样照搬 dl_ena.sh 的 4b 段
final_p="$T/out.fq.gz"
raw="$T/trunc.fq.gz"
nf="$T/.nrec"
ZIP="gzip"
t0=$(date +%s)
gzip -dc "$raw" 2>/dev/null | awk -v nf="$nf" '
  NR%4==1{a=$0}
  NR%4==2{b=$0}
  NR%4==3{c=$0}
  NR%4==0{ if(length($0)==length(b)){ printf "%s\n%s\n%s\n%s\n",a,b,c,$0; kept++ } else dropped++ }
  END{ printf "%d %d %d\n", kept+0, dropped+0, NR%4 > nf }
' | $ZIP > "${final_p}.tmp"
kept=""; dropped=""; tailrem=""
[ -f "$nf" ] && { read -r kept dropped tailrem < "$nf"; }
t1=$(date +%s)
printf '%s\n' "$kept" > "${final_p}.nrec"
mv "${final_p}.tmp" "$final_p"
echo
echo "✅ 裁尾完成｜耗时 $((t1-t0))s｜完整记录 ${kept}｜丢弃残条 ${dropped}｜残留行 ${tailrem}｜$(stat -c %s "$final_p") B"

# 4) 独立校验
echo
echo "--- 独立校验：产物是否整数条记录、末尾 SEQ/QUAL 是否等长 ---"
gzip -dc "$final_p" 2>/dev/null | awk '
  { n++; if(NR%4==2) ls=length($0); else if(NR%4==0 && length($0)!=ls) bad++ }
  END{ printf "  行数=%d  记录数=%d  行数余数=%d  长度不符=%d\n", n, n/4, n%4, bad+0 }'
gzip -dc "$final_p" 2>/dev/null | tail -4 | awk '{printf "  末条 len=%-4d %s\n", length($0), substr($0,1,50)}'
echo
echo "--- 与原始 FASTQ 前缀一致性（截断前应有的记录数）---"
gzip -dc "$final_p" 2>/dev/null > "$T/out.fq"
head -n "$((kept*4))" "$T/orig.fq" > "$T/orig_n.fq"
if cmp -s "$T/out.fq" "$T/orig_n.fq"; then echo "  ✅ 与原始前 $kept 条记录逐字节一致"; else echo "  ❌ 不一致"; fi
echo
echo "--- zcat 直读产物应无 EOF 报错 ---"
if gzip -t "$final_p" 2>&1 | grep -q .; then echo "  ❌ gzip 校验有报错"; else echo "  ✅ gzip 完整性通过（可被 zcat 无报错读完）"; fi
