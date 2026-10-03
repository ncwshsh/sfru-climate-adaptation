#!/usr/bin/env bash
# sf_pipeline.sh —— S. frugiperda 群体基因组核心管线（WSL Ubuntu-24.04 内运行）
#
# 用法:  bash sf_pipeline.sh [样本列表文件]      # 默认 /mnt/c/SF_data/01_raw/pilot_samples.txt
#        样本列表 = 每行一个 SRR 号
# 阶段:  FastQC -> bwa mem -> samtools sort/index -> samtools flagstat
#        -> bcftools mpileup|call 联合变异检测 -> 索引 + 统计 + 基础过滤
#
# 依赖: micromamba env `sfru`（已装 bwa 0.7.19 / samtools 1.24 / bcftools 1.24 / FastQC 0.12.1）
# 参考: /mnt/c/SF_data/03_align/ref_GCF_023101765.2.fna（bwa 索引 ref.* 已建）
#
# ⚠️ 状态: 脚本已写但【尚未实跑】——2026-09-15 晚 wsl.exe 被安全策略拦截，首次运行需人工确认。

set -euo pipefail

MM=/mnt/c/SF_data/tools/micromamba
export MAMBA_ROOT_PREFIX=/mnt/c/SF_data/tools/mamba
eval "$("$MM" shell hook -s bash)" || { echo "[ERR] micromamba hook 失败"; exit 1; }
micromamba activate sfru

REF_DIR=/mnt/c/SF_data/03_align
REF=${REF_DIR}/ref_GCF_023101765.2.fna
RAW=/mnt/c/SF_data/01_raw
QC=/mnt/c/SF_data/02_qc
ALN=/mnt/c/SF_data/03_align
VAR=/mnt/c/SF_data/04_variant
LIST=${1:-${RAW}/pilot_samples.txt}
THREADS=${THREADS:-16}
CALL_THREADS=${CALL_THREADS:-8}

# 临时目录必须显式指定到数据盘：若不指定，samtools 会把临时文件写进当前工作目录
# （上次因此把 710MB 的 tmp bam 掉进了百度同步盘）
TMP=/mnt/c/SF_data/tmp
mkdir -p "$QC" "$ALN" "$VAR" "$TMP"
[ -f "${REF}.fai" ] || { echo "[ERR] 缺参考索引 ${REF}.fai"; exit 1; }

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }

# 收集可用样本（R1/R2 均存在且非空）
OK=()
while read -r s; do
  [ -z "$s" ] && continue
  case "$s" in \#*) continue;; esac
  r1="${RAW}/${s}_1.fastq.gz"; r2="${RAW}/${s}_2.fastq.gz"
  if [ -s "$r1" ] && [ -s "$r2" ]; then OK+=("$s"); else log "跳过 $s（FASTQ 不完整）"; fi
done < "$LIST"

[ "${#OK[@]}" -eq 0 ] && { echo "[ERR] 无可用样本"; exit 1; }
log "进入管线的样本: ${OK[*]}"

BAMS=()
for s in "${OK[@]}"; do
  r1="${RAW}/${s}_1.fastq.gz"; r2="${RAW}/${s}_2.fastq.gz"
  bam="${ALN}/${s}.bam"

  # ---- 1. FastQC ----
  if [ ! -f "${QC}/${s}_1_fastqc.html" ]; then
    log "[${s}] FastQC"
    fastqc -t 4 -o "$QC" "$r1" "$r2" || log "[${s}] FastQC 警告（不阻断）"
  fi

  # ---- 2. 比对 ----
  if [ -s "$bam" ]; then
    log "[${s}] BAM 已存在，跳过比对"
  else
    log "[${s}] bwa mem -> sort"
    bwa mem -t "$THREADS" -M \
      -R "@RG\tID:${s}\tSM:${s}\tPL:ILLUMINA\tLB:${s}\tPU:unit1" \
      "$REF" "$r1" "$r2" \
      | samtools sort -@ 4 -m 2G -T "${TMP}/${s}" -o "${bam}.tmp" -
    mv "${bam}.tmp" "$bam"
  fi
  [ -f "${bam}.bai" ] || samtools index -@ 4 "$bam"

  samtools flagstat -@ 4 "$bam" > "${ALN}/${s}.flagstat"
  log "[${s}] $(grep -m1 'mapped (' "${ALN}/${s}.flagstat" | sed 's/^ *//')"

  # ---- 3. 重复标记（可选，默认开；内存不足可 DEDUP=0 关闭）----
  if [ "${DEDUP:-1}" = "1" ] && [ ! -s "${ALN}/${s}.dedup.bam" ]; then
    log "[${s}] markdup"
    samtools collate -@ 4 -T "${TMP}/${s}_col" -o - "$bam" | samtools fixmate -@ 4 -m - - \
      | samtools sort -@ 4 -m 2G -T "${TMP}/${s}_md" -o - - | samtools markdup -@ 4 - "${ALN}/${s}.dedup.bam"
    samtools index -@ 4 "${ALN}/${s}.dedup.bam"
  fi
  if [ -s "${ALN}/${s}.dedup.bam" ]; then BAMS+=("${ALN}/${s}.dedup.bam"); else BAMS+=("$bam"); fi
done

# ---- 4. 联合变异检测 ----
log "联合变异检测: ${#BAMS[@]} 个 BAM"
OUT=${VAR}/cohort$(date +%m%d)_raw.vcf.gz

# -d 是【每样本】的深度上限，默认 250；样本降到 10x 后绰绰有余，
# 但高深度样本（30-60x）需调高，否则会被静默截断
MAX_DEPTH=${MAX_DEPTH:-500}

bcftools mpileup -f "$REF" -a FORMAT/AD,FORMAT/DP,FORMAT/GQ -q 20 -Q 20 -d "$MAX_DEPTH" \
  --threads "$CALL_THREADS" -Ou "${BAMS[@]}" \
  | bcftools call -m -v --threads "$CALL_THREADS" -Oz -o "$OUT"
bcftools index -t "$OUT"

# ---- 5. 统计与过滤 ----
bcftools stats -F "$REF" -s - "$OUT" > "${OUT%.vcf.gz}.stats"
FLT=${OUT%.vcf.gz}_flt.vcf.gz
# ⚠️ 阈值必须按实测深度设：上次用 INFO/DP>20 时，5x 数据下只剩高深度重复区
#     （得到位点中位深度 413x 的假象）。这里改为可配置，默认适配 10x x N 样本
DPMIN=${DPMIN:-5}
DPMAX=${DPMAX:-2000}   # 上限 = 约 2x 期望总深度(样本数 x 10x)
bcftools filter -i "QUAL>30 && INFO/DP>=$DPMIN && INFO/DP<=$DPMAX && MQ>30" -Oz -o "$FLT" "$OUT"
bcftools index -t "$FLT"

# ---- 6. 质检：Ts/Tv（<1.8 说明假阳性过多，callset 不可用于生物学解读）----
log "质检 Ts/Tv（期望 1.8~2.1，越接近 0.5 假阳性越多）:"
bcftools view -H -m2 -M2 -v snps "$FLT" 2>/dev/null | awk -F'\t' '{
  r=toupper($4); a=toupper($5);
  if(length(r)!=1||length(a)!=1) next;
  if((r=="A"&&a=="G")||(r=="G"&&a=="A")||(r=="C"&&a=="T")||(r=="T"&&a=="C")) ts++; else tv++}
  END{if(ts+tv>0) printf "  Ts/Tv = %.2f  (ts=%d tv=%d)\n", ts/tv, ts, tv; else print "  无位点"}'

log "原始位点: $(bcftools view -H "$OUT" | wc -l)"
log "过滤后  : $(bcftools view -H "$FLT" | wc -l)"
log "完成 -> $FLT  (统计: ${OUT%.vcf.gz}.stats)"
