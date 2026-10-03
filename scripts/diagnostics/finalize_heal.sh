#!/bin/bash
# finalize_heal.sh —— 裁尾收尾（不含全量复查；结构复查见 sweep_structure.sh）
#  1) 把可见凭证 X.nrec 迁移为隐藏凭证 .nrec.X
#     原因：项目里多个脚本用 `ls ${s}_1.fastq.gz* | head -1` 选输入，
#           非隐藏 sidecar 会被 * 匹配 → 可能选中错误文件。点开头则天然不匹配。
#  2) 汇总记录数台账 fastq_records.tsv（文件 / 记录数 / 字节数）
export PATH="/usr/bin:/bin:$PATH"

DIRS="/mnt/c/SF_data/01_raw /mnt/c/SF_data/01_deep"
LEDGER=/mnt/c/SF_data/tools/fastq_records.tsv

echo "================ 1. 迁移凭证为隐藏文件 ================"
mig=0; orphan=0
for D in $DIRS; do
  for m in "$D"/*.nrec; do
    [ -f "$m" ] || continue
    b="$(basename "$m")"
    base="${b%.nrec}"
    if [ -f "${D}/${base}" ]; then
      mv "$m" "${D}/.nrec.${base}" && mig=$((mig+1))
    else
      echo "  [WARN] 孤儿凭证（无对应数据文件），保留原样: $b"
      orphan=$((orphan+1))
    fi
  done
done
echo "  已迁移 $mig 个；孤儿 $orphan 个"
echo "  剩余可见 .nrec = $(for D in $DIRS; do ls -1 "$D"/*.nrec 2>/dev/null; done | wc -l)"
echo "  隐藏凭证 .nrec.* = $(for D in $DIRS; do ls -1 "$D"/.nrec.* 2>/dev/null; done | wc -l)"

echo
echo "================ 2. 生成记录数台账 ================"
printf 'file\trecords\tbytes\n' > "$LEDGER"
for D in $DIRS; do
  for mk in "$D"/.nrec.*; do
    [ -f "$mk" ] || continue
    b="$(basename "$mk")"; base="${b#.nrec.}"
    f="${D}/${base}"
    [ -f "$f" ] || continue
    printf '%s\t%s\t%s\n' "$base" "$(tr -d '[:space:]' < "$mk")" "$(stat -c %s "$f")" >> "$LEDGER"
  done
done
echo "  台账: $(wc -l < "$LEDGER") 行（含表头）"
echo "  --- 前 6 行 ---"
head -6 "$LEDGER"
echo "  --- 合计记录数 ---"
awk -F'\t' 'NR>1{s+=$2} END{printf "  %.0f 条\n", s}' "$LEDGER"

echo
echo "================ 3. 目录盘点 ================"
echo "  01_raw  可见条目 = $(ls -1 /mnt/c/SF_data/01_raw | wc -l)   隐藏项 $(ls -1 /mnt/c/SF_data/01_raw/.??* 2>/dev/null | wc -l)"
echo "  01_deep 可见条目 = $(ls -1 /mnt/c/SF_data/01_deep | wc -l)   隐藏项 $(ls -1 /mnt/c/SF_data/01_deep/.??* 2>/dev/null | wc -l)"
echo "  01_raw  成品 .fastq.gz = $(ls -1 /mnt/c/SF_data/01_raw/*.fastq.gz 2>/dev/null | wc -l)"
echo "  01_raw  残片 .partial* = $(ls -1 /mnt/c/SF_data/01_raw/*.fastq.gz.partial[0-9]* 2>/dev/null | wc -l)"
echo "=== finalize done ==="
