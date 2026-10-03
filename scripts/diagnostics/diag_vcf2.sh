#!/usr/bin/env bash
# diag_vcf2.sh —— 判断假阳性来源：是否集中在未定位 scaffld / 低复杂度区（WSL 内运行）
set -u
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
eval "$("$MM" shell hook -s bash)"
micromamba activate sfru

VAR=/mnt/c/SF_data/04_variant
ALN=/mnt/c/SF_data/03_align
RAW=${VAR}/pilot_0915_raw.vcf.gz
FAI=${ALN}/ref_GCF_023101765.2.fna.fai

# 31 条染色体 = 长度 > 1Mb 的序列
awk '$2>1000000{print $1}' "$FAI" > /tmp/chroms.txt
echo "主染色体序列数: $(wc -l < /tmp/chroms.txt)"

echo
echo "########## 1. 变异位点在各类序列上的分布（原始 callset）##########"
bcftools index -s "$RAW" 2>/dev/null | awk '
  BEGIN{while((getline l < "/tmp/chroms.txt")>0) ch[l]=1}
  {if(ch[$1]) a+=$3; else b+=$3}
  END{printf "  主染色体(31条) : %d 位点\n  未定位/其他    : %d 位点\n  未定位占比     : %.1f%%\n", a, b, b/(a+b)*100}'

echo
echo "########## 2. 位点最多的 10 条序列 ##########"
bcftools index -s "$RAW" 2>/dev/null | sort -k3,3nr | head -10 | awk '{printf "  %-18s %10d 位点\n", $1, $3}'

echo
echo "########## 3. 逐样本基因型构成（QUAL>100 的双等位 SNP）##########"
bcftools filter -i 'QUAL>100' -Ou "$RAW" 2>/dev/null \
 | bcftools view -m2 -M2 -v snps -Ou 2>/dev/null \
 | bcftools query -f '[%GT ]\n' 2>/dev/null \
 | awk '{for(i=1;i<=NF;i++){g=$i;
        if(g=="0/0"||g=="0|0") hom_ref[i]++;
        else if(g=="0/1"||g=="0|1"||g=="1/0") het[i]++;
        else if(g=="1/1"||g=="1|1") hom_alt[i]++;
        else other[i]++}
        n++}
   END{
     for(i=1;i<=2;i++){
       t=hom_ref[i]+het[i]+hom_alt[i]+other[i]
       printf "  样本%d: 总%9d  纯合参考%9d  杂合%8d  纯合变异%8d  杂合率%.1f%%\n",
              i, t, hom_ref[i], het[i], hom_alt[i], het[i]/t*100
     }}'

echo
echo "########## 4. 限定主染色体后的 Ts/Tv ##########"
tstv() {
  bcftools view -H -m2 -M2 -v snps "$1" 2>/dev/null \
  | awk -F'\t' '{r=$4;a=$5;
      if((r=="A"&&a=="G")||(r=="G"&&a=="A")||(r=="C"&&a=="T")||(r=="T"&&a=="C")) ts++;
      else if(length(r)==1&&length(a)==1) tv++}
    END{printf "%.2f (位点 %d)", ts/tv, ts+tv}'
}
for cond in 'QUAL>100' 'QUAL>100 && INFO/DP>=4 && INFO/DP<=25' 'QUAL>200 && INFO/DP>=4 && INFO/DP<=25'; do
  bcftools filter -i "$cond" -Ou "$RAW" 2>/dev/null \
   | bcftools view -T /tmp/chroms.txt -m2 -M2 -Oz -o /tmp/chr.vcf.gz 2>/dev/null
  printf "  仅主染色体 + %-42s -> Ts/Tv %s\n" "$cond" "$(tstv /tmp/chr.vcf.gz)"
done
