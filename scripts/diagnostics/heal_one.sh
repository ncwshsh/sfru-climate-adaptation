#!/bin/bash
# heal_one.sh —— 对单个「按比例下载残片」就地裁尾（去尾部半条 FASTQ 记录）
# 用法: bash heal_one.sh <残片路径>
# 依赖: WSL 内的 pigz（免 root 安装于 ~/opt/pigz_root/usr/bin/pigz）
#
# 原理：gzip -dc | awk 只保留 length(QUAL)==length(SEQ) 的完整 4 行记录 | 重压
# 安全：先写临时文件 -> 校验 gzip 完整性 -> 再原子替换；任何一步失败都保留原文件
# 凭证：成功后写**隐藏**凭证 .nrec.<原名>（记录条数），供 dl_ena.sh / pick_fq 判定「已裁尾」而跳过
# ⚠️ 必须隐藏！（2026-09-17 修正）原写 <残片>.nrec 是非隐藏名，正好被 `X.fastq.gz*` 这类 glob 命中 ——
#    而项目里 4 个比对脚本用该 glob 选输入，且 pick_fq 只认隐藏的 .nrec.<原名> → 双向不一致。

PIGZ="${PIGZ:-$HOME/opt/pigz_root/usr/bin/pigz}"
TH="${TH:-8}"

f="$1"
[ -n "$f" ] || { echo "用法: bash heal_one.sh <残片路径>"; exit 2; }
[ -f "$f" ] || { echo "SKIP(不存在) $f"; exit 0; }
b="$(basename "$f")"
d="$(dirname "$f")"

case "$b" in
  .*) echo "SKIP(隐藏文件) $b"; exit 0 ;;
esac
case "$b" in
  *.part[0-9]|*.part[0-9][0-9]|*.part[0-9][0-9][0-9]) echo "SKIP(块文件) $b"; exit 0 ;;
esac
if [ -f "${d}/.nrec.${b}" ]; then echo "SKIP(已裁尾) $b"; exit 0; fi
# 兼容检查：旧的非隐藏凭证（若有残留也视为已裁尾，但不新写这种名字）
if [ -f "${f}.nrec" ]; then echo "SKIP(已裁尾·旧凭证) $b"; exit 0; fi

# 临时文件命名：抹掉点号，避免被 *.fastq.gz.partial* 的 glob 再次命中
tmp="${d}/.tmp_${b//./_}"

sz0=$(stat -c %s "$f")
nf=$(mktemp)
t0=$(date +%s)

"$PIGZ" -dc -p "$TH" "$f" 2>/dev/null | awk -v nf="$nf" '
  NR%4==1{a=$0}
  NR%4==2{b=$0}
  NR%4==3{c=$0}
  NR%4==0{ if(length($0)==length(b)){ printf "%s\n%s\n%s\n%s\n",a,b,c,$0; kept++ } else dropped++ }
  END{ printf "%d %d %d %d\n", kept+0, dropped+0, NR%4, NR > nf }
' | "$PIGZ" -p "$TH" -6 > "$tmp"

read -r kept dropped tailrem totlines < "$nf"
rm -f "$nf"
t1=$(date +%s)
kept="${kept:-0}"; dropped="${dropped:-0}"; tailrem="${tailrem:-0}"; totlines="${totlines:-0}"

if [ "$kept" -le 0 ]; then
  echo "FAIL(0条记录) $b  原文件保留"; rm -f "$tmp"; exit 1
fi

# 一致性自检：完整 4 行组数 == kept + dropped
groups=$(( (totlines - tailrem) / 4 ))
if [ $(( kept + dropped )) -ne "$groups" ]; then
  echo "WARN(计数不自洽) $b  kept=$kept dropped=$dropped groups=$groups"
fi

if ! "$PIGZ" -t "$tmp" 2>/dev/null; then
  echo "FAIL(gzip校验不过) $b  原文件保留"; rm -f "$tmp"; exit 1
fi

sz1=$(stat -c %s "$tmp")
mv "$tmp" "$f" && printf '%s\n' "$kept" > "${d}/.nrec.${b}"
echo "OK $b  完整记录=$kept  丢弃残条=$dropped  残留行=$tailrem  ${sz0} -> ${sz1} B  $((t1-t0))s  凭证=.nrec.${b}"
