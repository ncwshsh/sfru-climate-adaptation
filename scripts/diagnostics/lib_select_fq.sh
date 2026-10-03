#!/usr/bin/env bash
# lib_select_fq.sh —— 统一的 FASTQ 输入选择（单一真相源）
#
# 用法:
#   . /path/to/lib_select_fq.sh
#   r1=$(pick_fq "${RAW}/${s}_1.fastq.gz")
#
# ⚠️ 为什么废弃旧写法 `r1=$(ls ${RAW}/${s}_1.fastq.gz* | head -1)`
#    同一个样本常有多个候选，旧写法有三个坑：
#      1) 字典序选错：`.partial30` < `.partial60`，`head -1` 会选中**数据最少**的那个。
#         本项目真实踩过（run_kenya60.sh 的注释有记录）。
#      2) 块文件被选中：未完成合并的碎片 `X.fastq.gz.partial39.part17` 也匹配该 glob，
#         尺寸还可能是 16 MB 的一小块，喂进比对器必崩。
#      3) 未裁尾的残片被选中：按比例下载的 `.partialN` 尾部有**半条 FASTQ 记录**，
#         会让 minimap2 报 `SEQ and QUAL are of different length` 而崩。
#
# 本函数的选择规则（按优先级）：
#   A. 在「确定可用」的候选里取**体积最大**者
#        确定可用 = 有隐藏裁尾凭证 `.nrec.<文件名>`  或  文件名不带 `.partialN` 后缀（全量下载）
#      —— 用体积最大而不是字典序，才不会取到 30% 那份；
#         用「确定可用」过滤，才不会取到未裁尾的残片。
#   B. 若没有确定可用的候选，退而取体积最大者，并在 stderr 明确警告。
#
# 依赖: bash 4+、GNU ls（-S 按体积降序）。WSL 与 Git Bash 均可。

pick_fq() {
  local prefix="$1"
  local -a cand=() valid=()
  local f b d

  # 1) 收集候选：按体积降序，排除块文件（.partN 结尾）
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    cand+=("$f")
  done < <(ls -S "${prefix}"* 2>/dev/null | grep -vE '\.part[0-9]+$')

  if [ "${#cand[@]}" -eq 0 ]; then
    return 1
  fi

  # 2) 筛出「确定可用」
  for f in "${cand[@]}"; do
    b="$(basename "$f")"; d="$(dirname "$f")"
    if [ -f "${d}/.nrec.${b}" ]; then valid+=("$f"); continue; fi
    case "$b" in
      *.partial[0-9]|*.partial[0-9][0-9]) ;;      # 无凭证的残片 -> 不确定
      *) valid+=("$f") ;;                          # 无 .partial 后缀 -> 全量下载，可用
    esac
  done

  # cand 已按体积降序，故 valid[0] / cand[0] 都是各自集合里最大的
  if [ "${#valid[@]}" -gt 0 ]; then
    printf '%s\n' "${valid[0]}"
    return 0
  fi

  echo "  [WARN] $(basename "${cand[0]}") 没有裁尾凭证，可能是未处理的残片；" >&2
  echo "         尾部半条记录会让比对器崩。请先跑 heal_one.sh 裁尾。" >&2
  printf '%s\n' "${cand[0]}"
  return 0
}

# 便捷包装：直接给样本号与数据目录，返回 R1/R2
#   pick_fq_pair <RAW目录> <样本号>   ->  stdout 两行：R1 路径、R2 路径
pick_fq_pair() {
  local raw="$1" s="$2" r1 r2
  r1="$(pick_fq "${raw}/${s}_1.fastq.gz")" || return 1
  r2="$(pick_fq "${raw}/${s}_2.fastq.gz")" || return 1
  [ -n "$r1" ] && [ -n "$r2" ] || return 1
  printf '%s\n%s\n' "$r1" "$r2"
}
