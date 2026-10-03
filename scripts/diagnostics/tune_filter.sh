#!/usr/bin/env bash
# tune_filter.sh —— 用 Ts/Tv 作为判据，筛选合适的 VCF 过滤阈值（WSL 内运行）
# 真 SNP 的 Ts/Tv 应在 1.8~2.2；越接近 0.5 说明假阳性越多
set -u
MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
eval "$("$MM" shell hook -s bash)"
micromamba activate sfru

VAR=/mnt/c/SF_data/04_variant
RAW=${VAR}/pilot_0915_raw.vcf.gz

# Ts/Tv 计算：只取双等位 SNP
tstv() {
  bcftools view -H -m2 -M2 -v snps "$1" 2>/dev/null \
  | awk -F'\t' '{
      r=$4; a=$5;
      if ((r=="A"&&a=="G")||(r=="G"&&a=="A")||(r=="C"&&a=="T")||(r=="T"&&a=="C")) ts++;
      else if (length(r)==1 && length(a)==1) tv++;
    } END{
      n=ts+tv; if(n==0){print "NA NA 0"; exit}
      printf "%.2f %d %d", ts/tv, n, ts
    }'
}

printf "%-52s %8s %8s %8s\n" "过滤条件" "位点" "Ts/Tv" "转换数"
printf "%s\n" "---------------------------------------------------------------------------"

run() {
  label="$1"; expr="$2"
  out=/tmp/tune.vcf.gz
  bcftools filter -i "$expr" -Ou "$RAW" 2>/dev/null \
    | bcftools view -m2 -M2 -Oz -o "$out" 2>/dev/null
  bcftools index -t -f "$out" 2>/dev/null
  res=$(tstv "$out")
  n=$(echo "$res" | cut -d' ' -f2)
  r=$(echo "$res" | cut -d' ' -f1)
  printf "%-52s %8s %8s\n" "$label" "$n" "$r"
  rm -f "$out" "$out.tbi"
}

run "① 原始（不过滤）"                    'QUAL>=0'
run "② QUAL>20"                          'QUAL>20'
run "③ QUAL>50"                          'QUAL>50'
run "④ QUAL>100"                         'QUAL>100'
run "⑤ QUAL>50 + DP 5~40"                'QUAL>50 && INFO/DP>=5 && INFO/DP<=40'
run "⑥ QUAL>100 + DP 5~40"               'QUAL>100 && INFO/DP>=5 && INFO/DP<=40'
run "⑦ QUAL>100 + DP 5~40 + MQ>40"       'QUAL>100 && INFO/DP>=5 && INFO/DP<=40 && MQ>40'
run "⑧ QUAL>200 + DP 8~40"               'QUAL>200 && INFO/DP>=8 && INFO/DP<=40'
run "⑨ QUAL>100 + DP 5~40 + 双样本DP>=3" 'QUAL>100 && INFO/DP>=5 && INFO/DP<=40 && MIN(FMT/DP)>=3'
run "⑩ QUAL>100 + DP 5~40 + 双样本DP>=3 + MQB>0.1" 'QUAL>100 && INFO/DP>=5 && INFO/DP<=40 && MIN(FMT/DP)>=3'
