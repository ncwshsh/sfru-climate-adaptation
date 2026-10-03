#!/usr/bin/env bash
# call_cohort.sh —— 队列联合变异检测 + 质检（决定性关口：Ts/Tv 是否 ≥1.8）
#
# 用法: bash call_cohort.sh <BAM列表文件> [输出前缀]
#   BAM列表: 每行一个 BAM 的完整路径（WSL 路径，即 /mnt/c/...）
#
# 在 WSL Ubuntu-24.04 内运行。环境: /home/hugo/mamba/envs/sfru
set -uo pipefail

export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

# 数据已迁至 WSL 原生盘（读 /mnt/c 实测仅 3.2 MB/s，原生盘 123 MB/s）
DATA=${DATA:-/home/hugo/data}
REF=${REF:-${DATA}/ref/ref_GCF_023101765.2.fna}
VAR=${VAR:-${DATA}/04_variant}
TMP=${TMP:-${DATA}/tmp}
LIST="${1:?需要 BAM 列表文件}"
PREFIX="${2:-cohort}"
THREADS=${THREADS:-16}
MAX_DEPTH=${MAX_DEPTH:-500}     # 每样本 mpileup 深度上限
DPMIN=${DPMIN:-5}
DPMAX=${DPMAX:-2000}
OUT=${VAR}/${PREFIX}_raw.vcf.gz
FLT=${VAR}/${PREFIX}_flt.vcf.gz

mkdir -p "$VAR" "$TMP"
log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "${VAR}/${PREFIX}.log"; }

mapfile -t BAMS < <(grep -v '^#' "$LIST" | grep -v '^$')
NB=${#BAMS[@]}
[ "$NB" -eq 0 ] && { echo "[ERR] BAM 列表为空"; exit 1; }

# 校验 BAM 都存在
MISS=0
for b in "${BAMS[@]}"; do [ -s "$b" ] || { log "缺 BAM: $b"; MISS=1; }; done
[ "$MISS" -eq 1 ] && { log "[ERR] 有 BAM 缺失，终止"; exit 1; }

log "联合 call: ${NB} 个 BAM, MAX_DEPTH=${MAX_DEPTH}, 线程=${THREADS}"

# ---- mpileup + call ----
if [ ! -s "$OUT" ]; then
  log "bcftools mpileup + call 开始（这步最慢）"
  # ⚠️ mpileup 的 -a 只接受 AD/DP/SP 等 pileup 级 tag；GQ 是 call 阶段才产生的，必须放在 call 的 -a
  if ! bcftools mpileup -f "$REF" -a AD,DP \
       -q 20 -Q 20 -d "$MAX_DEPTH" --threads "$THREADS" -Ou "${BAMS[@]}" \
       | bcftools call -m -v -a GQ --threads "$THREADS" -Oz -o "$OUT"; then
    log "[ERR] mpileup/call 失败，清理残file后重试"
    rm -f "$OUT"
    exit 1
  fi
  # ⚠️ 不加退出码检查的话，空的/坏的 VCF 会被当成"完成"，下游全错
  if ! bcftools index -t "$OUT"; then
    log "[ERR] index 失败，VCF 不可用"
    rm -f "$OUT" "$OUT.tbi" "$OUT.csi"
    exit 1
  fi
  log "raw VCF: $OUT"
else
  log "raw VCF 已存在，跳过 call"
fi

# ---- 统计 ----
bcftools stats -F "$REF" -s - "$OUT" > "${VAR}/${PREFIX}_raw.stats"
log "=== RAW Ts/Tv ==="
grep -E 'Ts/Tv ratio|number of (transitions|transversions|SNPs|indels)' "${VAR}/${PREFIX}_raw.stats" | sed 's/^/  /'

# ---- 过滤 ----
bcftools filter -i "QUAL>30 && INFO/DP>=$DPMIN && INFO/DP<=$DPMAX && MQ>30" -Oz -o "$FLT" "$OUT"
bcftools index -t "$FLT"
bcftools stats -F "$REF" -s - "$FLT" > "${VAR}/${PREFIX}_flt.stats"

log "=== 过滤后 Ts/Tv（QUAL>30, ${DPMIN}<=DP<=${DPMAX}, MQ>30）==="
grep -E 'Ts/Tv ratio|number of (transitions|transversions|SNPs|indels)' "${VAR}/${PREFIX}_flt.stats" | sed 's/^/  /'

# ---- 基因型构成（0/0 应占多数；若 1/1 最多说明基因型错得离谱）----
log "=== 基因型构成（过滤后）==="
bcftools query -f '[%GT ]\n' "$FLT" 2>/dev/null | tr ' ' '\n' | grep -v '^$' \
  | sort | uniq -c | sort -rn | head -8 | sed 's/^/  /'

# ---- 判定 ----
TSTV=$(grep 'Ts/Tv ratio' "${VAR}/${PREFIX}_flt.stats" | grep -oP 'Ts/Tv ratio:\s*\K[0-9.]+')
if [ -z "$TSTV" ]; then log "[ERR] 未能解析 Ts/Tv，stats 为空或格式异常"; exit 1; fi
NSNP=$(grep -m1 'number of SNPs' "${VAR}/${PREFIX}_flt.stats" | grep -oP ':\s*\K[0-9]+')
log "过滤后 SNP 数: ${NSNP}   Ts/Tv: ${TSTV}"
if awk "BEGIN{exit !($TSTV >= 1.8)}"; then
  log "✅ Ts/Tv = ${TSTV} ≥ 1.8 —— callset 可用于下游分析"
else
  log "❌ Ts/Tv = ${TSTV} < 1.8 —— 假阳性过多，10x 数据或未达标，需提高深度/样本数后重试"
fi
log "完成 -> $FLT"
