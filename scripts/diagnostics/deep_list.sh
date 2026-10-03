#!/usr/bin/env bash
# deep_list.sh —— 生成「深度 >=20x 样本清单」，含拿到 25x 所需文件比例
export PATH="/usr/bin:/bin:$PATH"
M=/c/SF_data/tools/sfru_wgs_matrix.tsv
OUT=/c/SF_data/tools/deep_picks_20x.tsv

printf "%-14s\t%-14s\t%-16s\t%-22s\t%-8s\t%10s\t%8s\t%10s\n" \
  run study region country layout depth_x pct_25x est_GB_25x > "$OUT"
awk -F'\t' 'NR==1{for(i=1;i<=NF;i++)h[$i]=i; next}
{
  d=$h["depth_x"]+0; if(d<20) next
  b=$h["bases"]+0
  pct = 25/d*100
  # 估字节：碱基 / 1.7 (bp per compressed byte)
  gb = 25*384e6/1.7/1e9
  printf "%-14s\t%-14s\t%-16s\t%-22s\t%-8s\t%10.2f\t%7.1f%%\t%10.2f\n", \
    $h["run"], $h["study"], $h["region"], $h["country"], $h["layout"], d, pct, gb
}' "$M" | sort -k6,6n > /tmp/_dl.txt

cat /tmp/_dl.txt >> "$OUT"

echo "深度>=20x 样本数: $(wc -l < /tmp/_dl.txt)"
echo
echo "=== 按地区 ==="
awk -F'\t' '{c[$3]++} END{for(k in c) printf "  %-16s %d\n", k, c[k]}' /tmp/_dl.txt | sort -k2,2rn
echo
echo "=== 按布局 ==="
awk -F'\t' '{c[$5]++} END{for(k in c) printf "  %-10s %d\n", k, c[k]}' /tmp/_dl.txt
echo
echo "=== 深度分档 ==="
awk -F'\t' '{d=$6+0; if(d<30) k="20-30x"; else if(d<40) k="30-40x"; else if(d<60) k="40-60x"; else if(d<100) k="60-100x"; else k=">=100x"; c[k]++}
END{split("20-30x 30-40x 40-60x 60-100x >=100x",o," "); for(i=1;i<=5;i++) printf "  %-10s %d\n", o[i], c[o[i]]+0}' /tmp/_dl.txt
echo
echo "=== 地区 x 深度 交叉（只看 >=40x，最适合做深样本）==="
awk -F'\t' '$6+0>=40 {c[$3]++} END{for(k in c) printf "  %-16s %d 个\n", k, c[k]}' /tmp/_dl.txt | sort -k2,2rn
echo
echo "已写出: $OUT"