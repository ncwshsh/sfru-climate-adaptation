#!/usr/bin/env bash
# pick_deep.sh —— 扫描深样本，按「压缩率 bp/byte」排序，找拿 20x 覆盖最省字节的样本
export PATH="/usr/bin:/bin:$PATH"
PROXY="http://127.0.0.1:7897"
M=/c/SF_data/tools/sfru_wgs_matrix.tsv
OUT=/c/SF_data/tools/_deep_cand.tsv

# 取深度 >= 60 的全部样本
awk -F'\t' 'NR==1{for(i=1;i<=NF;i++)h[$i]=i; next}
{d=$h["depth_x"]+0; if(d>=60) print $h["run"]"\t"d"\t"$h["region"]"\t"$h["country"]"\t"$h["study"]"\t"$h["layout"]}
' "$M" | sort -k2,2 -rn > "$OUT"
N=$(wc -l < "$OUT")
echo "深度>=60x 的样本数: $N"
echo -e "run\tdepth_x\tregion\tcountry\tstudy\tlayout\tbp_per_byte\tbytes_for_20x_GB" > _deep_ratio.tsv

i=0
while IFS=$'\t' read -r run dep reg ctry study lay; do
  i=$((i+1))
  [ $i -gt 40 ] && break
  r=$(curl -s --max-time 20 -x "$PROXY" \
    "https://www.ebi.ac.uk/ena/portal/api/filereport?accession=${run}&result=read_run&fields=base_count,fastq_bytes,library_layout&format=tsv" 2>/dev/null | tail -n +2)
  [ -z "$r" ] && { echo "  [skip] $run 无元数据"; continue; }
  bc=$(printf '%s' "$r" | cut -f1)
  fb=$(printf '%s' "$r" | cut -f2 | tr ';' '+' | sed 's/$/0/')
  tot_bytes=$(awk -v s="$fb" 'BEGIN{n=split(s,a,"+"); t=0; for(k=1;k<=n;k++) t+=a[k]; print t}')
  ratio=$(awk -v b="$bc" -v y="$tot_bytes" 'BEGIN{ if(y>0) printf "%.3f", b/y; else print 0 }')
  gb20=$(awk -v r="$ratio" 'BEGIN{ if(r>0) printf "%.2f", (20*384e6)/r/1e9; else print "NA" }')
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$run" "$ratio" "$gb20" "$dep" "$reg" "$ctry" >> _deep_ratio.tsv
  printf "  [%2d/%2d] %s dep=%sx ratio=%s bp/B -> 20x 需 %s GB\n" "$i" "$N" "$run" "$dep" "$ratio" "$gb20"
done < "$OUT"

echo
echo "===== 按 20x 字节成本升序（最省在前）====="
echo -e "run\tratio\tdep\tGB_for_20x\tregion\tcountry"
awk -F'\t' 'NR>1{print $1"\t"$2"\t"$4"\t"$3"\t"$5"\t"$6}' _deep_ratio.tsv | sort -k4,4n | head -15
