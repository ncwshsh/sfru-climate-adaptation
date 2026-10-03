#!/usr/bin/env bash
# diag_polyg.sh —— 量化每个样本「未比对 reads」的性质：平均 G 含量 + polyG(>=20) 比例
# 用法（WSL 内）: bash /mnt/c/SF_data/tools/diag_polyg.sh
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
B=/mnt/c/SF_data/03_align
OUT=/mnt/c/SF_data/tools/diag_polyg.tsv

printf "SRR\tmapped_pct\tunmap_G_pct\tunmap_polyG20_pct\n" > "$OUT"

for bam in "$B"/*.dedup.bam; do
  S=$(basename "$bam" .dedup.bam)
  [ -s "$B/$S.flagstat" ] || continue
  rate=$(grep 'primary mapped (' "$B/$S.flagstat" | grep -oP '\d+\.\d+(?=%)')
  read gpct pgpct <<<"$(samtools view -f4 "$bam" 2>/dev/null | head -20000 | awk '
    { s=$10; n=length(s); if(n==0) next
      c=0; for(i=1;i<=n;i++) if(substr(s,i,1)=="G") c++
      sum+=c/n
      if (s ~ /G{20,}/) pg++
      tot++
    }
    END{ if(tot==0) print "NA NA"; else printf "%.1f %.1f", sum*100/tot, pg*100/tot }')"
  printf "%s\t%s\t%s\t%s\n" "$S" "$rate" "$gpct" "$pgpct" >> "$OUT"
done

echo "--- 全部样本（按比对率升序）---"
tail -n +2 "$OUT" | sort -t$'\t' -k2 -n | awk -F'\t' '{
  v = ($3+0 >= 45) ? "技术假象(polyG)" : (($2+0 < 88) ? "疑似污染/物种问题" : "ok")
  printf "  %-14s 比对率 %-6s 未比对G %-5s%% polyG20 %-5s%%  %s\n",$1,$2,$3,$4,v }'
