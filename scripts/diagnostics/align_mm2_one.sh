#!/usr/bin/env bash
# align_mm2_one.sh —— 单样本比对（minimap2 版，短读长模式 -ax sr）
# bwa mem 每样本约需 11572 秒 CPU；minimap2 对短读长通常快 3-10 倍，
# 317 个样本的差异是 51 小时 vs 10 小时级别，故改用 minimap2。
# 用法: bash align_mm2_one.sh <SRR>
set -uo pipefail
# ⚠️ pipefail 必须开：samtools collate 曾因 "-o 与 -O 冲突" 静默失败，
#    管道把空流喂给 markdup，最终产出 28 字节的空 BAM 而脚本报 DONE。
# 环境：micromamba sfru @ WSL 原生盘（/mnt/c 下的旧 env 不存在，勿再用）
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH

s="$1"
# 数据根目录：默认走 WSL 原生盘（读 /mnt/c 实测仅 3.2 MB/s，原生盘 cp 可达 123 MB/s）
DATA=${DATA:-/home/hugo/data}
REF=${REF:-${DATA}/ref/ref_GCF_023101765.2.fna}
MMI=${REF}.mmi
RAW=${RAW:-${DATA}/01_raw}
ALN=${ALN:-${DATA}/03_align}
TMP=${TMP:-${DATA}/tmp}
THREADS=${THREADS:-4}

# FASTQ 输入选择：统一走 lib_select_fq.sh（不再用 `ls ... | head -1`）
# 旧写法有三个坑：字典序会选中数据最少的 .partial30；块文件 .partN 会被误选；
# 未裁尾的残片尾部有半条记录会让比对器崩。详见 lib_select_fq.sh 注释。
_libdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FQLIB="${FQLIB:-${_libdir}/lib_select_fq.sh}"
[ -f "$FQLIB" ] || { echo "[$s] FAIL 缺 FASTQ 选择库 $FQLIB"; exit 1; }
. "$FQLIB"
r1=$(pick_fq "${RAW}/${s}_1.fastq.gz")
r2=$(pick_fq "${RAW}/${s}_2.fastq.gz")
if [ -z "$r1" ] || [ -z "$r2" ]; then
  echo "[$s] SKIP 缺 FASTQ"
  exit 0
fi
echo "[$s] 输入 R1=$(basename "$r1")  R2=$(basename "$r2")"
if [ -s "${ALN}/${s}.dedup.bam" ]; then
  echo "[$s] SKIP 已有 dedup.bam"
  exit 0
fi

mkdir -p "$TMP"
tmpbam="${TMP}/${s}.bam"

# 索引只建一次（并发安全：先写临时名再原子改名）
if [ ! -s "$MMI" ]; then
  minimap2 -x sr -d "${MMI}.tmp.$$" "$REF" 2>/dev/null && mv "${MMI}.tmp.$$" "$MMI"
fi

minimap2 -ax sr -t "$THREADS" \
  -R "@RG\tID:${s}\tSM:${s}\tPL:ILLUMINA\tLB:${s}\tPU:unit1" \
  "$MMI" "$r1" "$r2" 2>/dev/null \
  | samtools sort -@ 2 -m 1G -T "${TMP}/${s}_s" -o "$tmpbam" -

if [ ! -s "$tmpbam" ]; then
  echo "[$s] FAIL 比对未产出"
  rm -f "$tmpbam"
  exit 1
fi

# ⚠️ samtools 1.24 起 collate 的 -O 与 -o 互斥，只能用 -o -
samtools collate -@ 2 -T "${TMP}/${s}_c" -o - "$tmpbam" \
  | samtools fixmate -@ 2 -m - - \
  | samtools sort -@ 2 -m 1G -T "${TMP}/${s}_md" -o - - \
  | samtools markdup -@ 2 - "${ALN}/${s}.dedup.bam"

# ⚠️ 必须先把 PIPESTATUS 拷出来：一旦执行任何别的命令，它就被覆盖，
#    在 set -u 下二次访问会触发 "unbound variable" 而误判失败
PS=("${PIPESTATUS[@]}")
if [ "${PS[0]:-0}" -ne 0 ] || [ "${PS[3]:-0}" -ne 0 ]; then
  echo "[$s] FAIL markdup 管道出错 (collate=${PS[0]:-?} markdup=${PS[3]:-?})"
  rm -f "${ALN}/${s}.dedup.bam"
  exit 1
fi

# 成品必须通过 quickcheck 且体积合理（> 1MB），否则视为坏文件
if ! samtools quickcheck "${ALN}/${s}.dedup.bam" 2>/dev/null || [ "$(stat -c%s "${ALN}/${s}.dedup.bam")" -lt 1048576 ]; then
  echo "[$s] FAIL 产出 BAM 校验不过或体积异常"
  rm -f "${ALN}/${s}.dedup.bam"
  exit 1
fi

samtools index -@ 2 "${ALN}/${s}.dedup.bam"
samtools flagstat -@ 2 "${ALN}/${s}.dedup.bam" > "${ALN}/${s}.flagstat"
rate=$(grep -m1 'mapped (' "${ALN}/${s}.flagstat" | sed 's/.*(\([0-9.]*%\).*/\1/')
rm -f "$tmpbam"
echo "[$s] DONE mm2 比对率 ${rate}"
