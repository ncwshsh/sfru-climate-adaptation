#!/usr/bin/env bash
export PATH=/usr/bin:/bin:$PATH
cd /c/SF_data/tools

echo "########## OTHER 类文库里，像基因组数据的 ##########"
echo "判据：Illumina + PAIRED + 每 spot 150-300 bp + base_count>=10Gbp(约26x)"
awk -F'\t' '
NR==1{next}
$3=="OTHER" && $8=="ILLUMINA" && $5=="PAIRED" {
  bc=$6+0; rc=$7+0
  if(rc<=0) next
  bp=bc/rc                       # 每 spot 碱基数
  x=bc/383923118                 # 名义深度
  if(bp>=140 && bp<=320 && x>=20){
    printf "%-14s %-14s %-9s bp/spot=%-7.1f depth=%6.1fx reads=%-11d\n", $1,$2,$8,bp,x,rc
    n++; if(x>mx) mx=x
  }
  t++
}
END{ printf "\n合计：OTHER+ILLUMINA+PAIRED 共 %d 个；其中疑似基因组且 >=20x 的 %d 个\n", t, n }
' all_sfru.tsv | sort -t= -k4 -rn | head -40
