#!/usr/bin/env bash
export PATH=/usr/bin:/bin:$PATH
cd /c/SF_data/tools

echo "########## 1. PRJNA1184410 概况 ##########"
curl -s "https://www.ebi.ac.uk/ena/portal/api/filereport?accession=PRJNA1184410&result=read_run&fields=run_accession,scientific_name,tax_id,library_strategy,library_source,instrument_platform,base_count,read_count,country&format=tsv" -o p1184410.tsv
echo "行数(含表头)=$(wc -l < p1184410.tsv)"
head -3 p1184410.tsv

echo
echo "########## 2. 全库 S. frugiperda (taxid 7108) 检索 ##########"
Q='tax_eq(7108)'
curl -s "https://www.ebi.ac.uk/ena/portal/api/search?result=read_run&query=${Q}&fields=run_accession,study_accession,library_strategy,library_source,library_layout,base_count,read_count,instrument_platform&format=tsv" -o all_sfru.tsv
echo "总 run 数=$(($(wc -l < all_sfru.tsv)-1))"
echo "--- 按 library_strategy ---"
awk -F'\t' 'NR>1{c[$3]++} END{for(k in c) printf "  %-16s %d\n", k, c[k]}' all_sfru.tsv | sort -k2 -rn
echo "--- 按 study 数 ---"
awk -F'\t' 'NR>1{s[$2]=1} END{print "  studies="length(s)}' all_sfru.tsv

echo
echo "########## 3. 与现有矩阵对比：矩阵漏了哪些 study ##########"
awk -F'\t' 'NR>1{print $2}' all_sfru.tsv | sort -u > _ena_studies.txt
awk -F'\t' 'NR>1{print $2}' sfru_wgs_matrix.tsv | sort -u > _mtx_studies.txt
echo "ENA 独有 study 数=$(comm -23 _ena_studies.txt _mtx_studies.txt | wc -l)"
echo "矩阵独有 study 数=$(comm -13 _ena_studies.txt _mtx_studies.txt | wc -l)"
echo "--- ENA 独有（矩阵漏掉的）前 20 个 ---"
comm -23 _ena_studies.txt _mtx_studies.txt | head -20
