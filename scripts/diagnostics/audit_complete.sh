#!/usr/bin/env bash
# audit_complete.sh —— 逐个比对磁盘 .fastq.gz 与 ENA 声明字节数，判定完整性
export PATH="/usr/bin:/bin:$PATH"
D=/c/SF_data/01_raw
PROXY="http://127.0.0.1:7897"
OUT=/c/SF_data/tools/_completeness.tsv
TMP=/c/SF_data/tools/_ena_bytes.txt

# 1. 收集磁盘上的成品文件（排除 partial/part）
ls -l "$D" 2>/dev/null | awk '/\.fastq\.gz$/{print $NF"\t"$5}' | sort > /c/SF_data/tools/_disk_files.tsv
echo "磁盘成品文件数: $(wc -l < /c/SF_data/tools/_disk_files.tsv)"

# 2. 取唯一 accession
cut -f1 /c/SF_data/tools/_disk_files.tsv | sed -E 's/_[12]\.fastq\.gz$//' | sort -u > /c/SF_data/tools/_acc.txt
N=$(wc -l < /c/SF_data/tools/_acc.txt)
echo "唯一 accession 数: $N"

# 3. 逐个查 ENA 声明字节
: > "$TMP"
i=0
while read -r acc; do
  i=$((i+1))
  r=$(curl -s --max-time 20 -x "$PROXY" \
    "https://www.ebi.ac.uk/ena/portal/api/filereport?accession=${acc}&result=read_run&fields=fastq_bytes&format=tsv" 2>/dev/null | tail -n +2 | cut -f2)
  printf "%s\t%s\n" "$acc" "$r" >> "$TMP"
  [ $((i % 20)) -eq 0 ] && echo "  ...已查 $i/$N"
done < /c/SF_data/tools/_acc.txt
echo "ENA 查询完成: $(wc -l < "$TMP") 条"

# 4. 比对
echo
echo "===================== 完整性判定 ====================="
printf "%-14s %-6s %14s %14s %8s  %s\n" "样本" "mate" "磁盘字节" "ENA声明" "完整度" "判定"
awk -F'\t' '
FNR==NR{ n=split($2,a,";"); for(k=1;k<=n;k++) ena[$1"_"k]=a[k]; next }
{
  f=$1; sz=$2
  acc=f; sub(/_[12]\.fastq\.gz$/,"",acc)
  mate=substr(f,length(acc)+2,1)
  e=ena[acc"_"mate]+0
  if(e>0){ pct=100*sz/e; j=(sz>=e*0.999)?"完整":(sz>=e*0.5?"截断":"严重截断") }
  else { pct=0; j="ENA无数据" }
  printf "%-14s %-6s %14d %14d %7.1f%%  %s\n", acc, mate, sz, e, pct, j
  if(j=="完整") full++; else if(j=="截断") part++; else if(j=="严重截断") bad++; else unk++
  tot+=sz; if(e>0){ have+=sz; want+=e }
}
END{
  print ""
  printf "  完整: %d 个文件\n", full+0
  printf "  截断: %d 个文件\n", part+0
  printf "  严重截断: %d 个文件\n", bad+0
  printf "  ENA无数据/查不到: %d 个文件\n", unk+0
  printf "  磁盘总量 %.2f GB / ENA应有 %.2f GB = %.1f%%\n", tot/1e9, want/1e9, 100*tot/want
}
' "$TMP" /c/SF_data/tools/_disk_files.tsv
