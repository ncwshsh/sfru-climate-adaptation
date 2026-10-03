#!/usr/bin/env bash
# ==============================================================================
# run_sens_excl3.sh —— 敏感性分析：剔除 3 个映射率 <70% 的样本，重跑跨国对比
#
# 用法（在 Windows PowerShell / CMD 里）：
#   wsl -d Ubuntu-24.04 -- bash /mnt/c/SF_data/tools/run_sens_excl3.sh
#
# 背景：分析队列（n=214）里仍有 3 个样本映射率 <70%（口径没执行干净）：
#   SRR9289294 60.19% (BR-C) / SRR12044624 68.87% (AM-C) / SRR9289279 69.87% (BR-C)
#   三个都是玉米型 ⇒ 剔除后 BR-C 24→22、AM-C 14→13，US/AF/CN 不变。
#   ⇒ 主结果（US 模块 RDA + 模块富集）与这 3 个样本无关，本脚本只检验 §3.9 跨国对比稳不稳。
#
# 安全性：所有输出带 _excl3 后缀，**不覆盖原结果**。
# ==============================================================================
set -uo pipefail
export PATH=/home/hugo/mamba/envs/gea/bin:$PATH

REP=/mnt/c/SF_data/tools/report
EXCL=$REP/exclude_lowmap3.txt

cat > "$EXCL" <<'EOF'
# 映射率 <70% 的残留样本（2026-09-24 敏感性分析）
SRR9289294
SRR12044624
SRR9289279
EOF

echo "=============================================="
echo "敏感性分析：剔除 3 个低映射率玉米型样本"
echo "排除清单: $EXCL"
echo "=============================================="

cd /mnt/c/SF_data/tools || exit 1
export EXCL_FILE="$EXCL"
export SUFFIX=_excl3

echo
echo "===== 1/2  分地区 partial RDA（重算 z）====="
python gea_crossregion.py
rc1=$?

echo
echo "===== 2/2  同口径候选基因集比较 ====="
python crossregion_genes.py
rc2=$?

echo
echo "===== 与原结果对照：分地区 RDA 汇总 ====="
printf '%-8s %-28s %-28s\n' "文件" "gea_crossregion.tsv" "gea_crossregion_excl3.tsv"
if [ -f "$REP/gea_crossregion.tsv" ] && [ -f "$REP/gea_crossregion_excl3.tsv" ]; then
  paste "$REP/gea_crossregion.tsv" "$REP/gea_crossregion_excl3.tsv" | \
    awk -F'\t' '{printf "%-8s n=%-4s R2=%-7s p=%-7s | n=%-4s R2=%-7s p=%-7s\n", $1,$2,$3,$4,$10,$11,$12}'
else
  echo "  缺文件，跳过对照"
fi

echo
echo "===== 与原结果对照：≥3 地区共享基因数 ====="
for f in crossregion_genes.tsv crossregion_genes_excl3.tsv; do
  if [ -f "$REP/$f" ]; then
    n3=$(awk -F'\t' 'NR>1 && $3>=3' "$REP/$f" | wc -l)
    tot=$(awk -F'\t' 'NR>1' "$REP/$f" | wc -l)
    echo "  $f : 总基因 $tot ，其中 ≥3 地区共享 $n3"
  else
    echo "  $f : 不存在"
  fi
done

echo
if [ "$rc1" = "0" ] && [ "$rc2" = "0" ]; then
  echo ">>> 敏感性分析完成，结果见 *${SUFFIX}.* "
else
  echo ">>> 有脚本返回非 0（$rc1 / $rc2），请检查上面的报错"
fi
