#!/usr/bin/env bash
# per_seq_depth.sh —— 逐条序列实测深度，找出「谁在拉高全库平均」
# 用法: bash per_seq_depth.sh <BAM>
set -uo pipefail
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
BAM="${1:?需要 BAM}"
REF=/home/hugo/data/ref/ref_GCF_023101765.2.fna
Fai="${REF}.fai"
AVG=$(samtools idxstats "$BAM" | awk '{m+=$3; l+=$2} END{print m*151/l}')

echo "全库均值（含重复） = $(printf '%.2f' "$AVG") x"
echo
echo "序号  序列              长度(bp)      比对reads    深度(x)   占全库碱基"
echo "---------------------------------------------------------------------------------"
samtools idxstats "$BAM" | awk -v fai="$Fai" -v avg="$AVG" '
BEGIN{
  while((getline line < fai) > 0){ split(line,a,"\t"); L[a[1]]=a[2]+0; ord[a[1]]=(++k); NAME[k]=a[1] }
  close(fai)
}
{
  name=$1; len=$2+0; map=$3+0
  if(len==0) next
  d[name]=map*151/len
  tot+=len
  allmap+=map
}
END{
  # 按长度降序
  n=0
  for(nm in d) arr[++n]=nm
  for(i=1;i<=n;i++) for(j=i+1;j<=n;j++) if(L[arr[j]]>L[arr[i]]){t=arr[i];arr[i]=arr[j];arr[j]=t}
  for(i=1;i<=n;i++){
    nm=arr[i]
    printf "%-5s %-20s %12d %12.0f %8.2f   %5.2f%%", ord[nm]"" , nm, L[nm], d[nm]*L[nm]/151, d[nm], 100*L[nm]/tot
    if(i<=31) printf "   <= 染色体\n"; else printf "\n"
  }
  # 分组统计
  c_l=0;c_m=0;s_l=0;s_m=0
  for(i=1;i<=n;i++){ nm=arr[i]
    if(ord[nm]<=31 && L[nm]>1000000){ c_l+=L[nm]; s_l+=d[nm]*L[nm] }
    else { c_m+=L[nm]; s_m+=d[nm]*L[nm] }
  }
  printf "\n=== 分组 ===\n"
  printf "染色体(前31条, >1Mb)   %12d bp  均值 %.2f x\n", c_l, s_l/c_l
  printf "其余(scaffold等)       %12d bp  均值 %.2f x\n", c_m, s_m/c_m
  printf "合计                   %12d bp  均值 %.2f x\n", c_l+c_m, (s_l+s_m)/(c_l+c_m)
}'
