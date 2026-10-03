#!/bin/bash
# 输出 01_raw / 01_deep 全量文件清单：size<TAB>mtime<TAB>path
export PATH="/usr/bin:/bin:$PATH"
OUT=/c/SF_data/tools/inv_storage.tsv
: > "$OUT"
for D in /c/SF_data/01_raw /c/SF_data/01_deep; do
  find "$D" -maxdepth 1 -type f -printf '%s\t%TY-%Tm-%Td %TH:%TM\t%p\n' 2>/dev/null >> "$OUT"
done
wc -l "$OUT"
echo "--- head ---"
head -3 "$OUT"
