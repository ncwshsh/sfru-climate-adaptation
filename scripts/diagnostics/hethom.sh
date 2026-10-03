export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
TAB=/home/hugo/data/tmp/gate.tab
echo "===== 按位点深度：杂合/纯合比 + alt 支持率分布（判断是否塌缩重复）====="
awk -F'\t' '
{
  dp=$6+0
  if(dp<10) k="DP_lt10"; else if(dp<20) k="DP_10_20"; else if(dp<45) k="DP_20_45"; else if(dp<90) k="DP_45_90"; else k="DP_gt90"
  het=0; hom=0
  for(i=7;i<=NF;i++){
    g=$i; if(g==""||g==".") continue
    gsub(/\|/,"/",g)
    if(g ~ /\//){ split(g,a,"/")
      if(a[1]!="."&&a[2]!="."){
        if(a[1]==a[2]) hom++; else het++
      }
    } else { if(g!=".") hom++ }
  }
  HET[k]+=het; HOM[k]+=hom; NDS[k]++
  HET["ALL"]+=het; HOM["ALL"]+=hom; NDS["ALL"]++
}
END{
  split("ALL DP_lt10 DP_10_20 DP_20_45 DP_45_90 DP_gt90", o, " ")
  printf "  %-10s %10s %12s %12s %8s\n","DP档","位点","杂合GT","纯合GT","het/hom"
  for(i=1;i<=6;i++){ k=o[i]
    printf "  %-10s %10d %12d %12d %8.3f\n", k, NDS[k]+0, HET[k]+0, HOM[k]+0, (HOM[k]>0? HET[k]/HOM[k] : 0)
  }
}
' "$TAB"

echo
echo "===== 关键对照：把所有 DP>45 的位点剥离后，整体 Ts/Tv ====="
awk -F'\t' '
function ists(r,a){ return ((r=="A"&&a=="G")||(r=="G"&&a=="A")||(r=="C"&&a=="T")||(r=="T"&&a=="C")) }
{
  r=$3;a=$4;dp=$6+0
  if(length(r)!=1||length(a)!=1||r==a) next
  ist=ists(r,a)
  if(dp<=45){ N["mid"]++; if(ist) TS["mid"]++; else TV["mid"]++ }
  else      { N["deep"]++; if(ist) TS["deep"]++; else TV["deep"]++ }
  N["all"]++; if(ist) TS["all"]++; else TV["all"]++
}
END{
  split("all mid deep", o, " ")
  for(i=1;i<=3;i++){ k=o[i]; v=TV[k]+0
    printf "  %-6s n=%-9d Ts=%-9d Tv=%-9d Ts/Tv=%.3f\n", k, N[k]+0, TS[k]+0, v, (v>0? (TS[k]+0)/v : 0) }
}
' "$TAB"
