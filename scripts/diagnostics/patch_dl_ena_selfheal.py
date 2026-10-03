#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
patch_dl_ena_selfheal.py —— 给 dl_ena.sh 打「结构性损坏自愈」补丁（幂等）

问题（2026-09-18 夜间实测）：
  4b-1 内容校验发现 bad>0 时，只把成品 mv 成 .bad.<base>，
  **没有删除对应的 .partN 块文件**。
  而这些块是「尺寸达标、内容错」，下一轮按 `stat -c %s >= exp` 判据会被直接复用，
  cat 出同样的坏内容 → 再次 bad → 再次 .bad → **死循环**，人工不介入永远好不了。

修复：
  在 bad>0 分支里，隔离成品的同时把 $parts（全部 .partN）删掉（每批 40，避开安全策略），
  强制下一轮真正重下载。

幂等：检测到补丁特征串 "自愈补丁" 就跳过，不重复插入。
"""
import io, sys

P = r"C:\SF_data\tools\dl_ena.sh"

OLD = '''      mv "${final_p}.tmp" "${OUT_POSIX}/.bad.${base}" 2>/dev/null || rm -f "${final_p}.tmp"
      overall=1; continue'''

NEW = '''      mv "${final_p}.tmp" "${OUT_POSIX}/.bad.${base}" 2>/dev/null || rm -f "${final_p}.tmp"
      # ★ 自愈补丁（2026-09-18 夜间）：结构损坏时所有块「尺寸达标、内容错」，
      #   若留着它们，下一轮会按 `size >= exp` 直接复用 → cat 出同样的坏内容 → 再次 .bad，死循环。
      #   故隔离成品的同时删掉 .partN（每批 40，避开 BULK 安全策略阈值 50），强制下一轮重下。
      if [ "$INPLACE" = "0" ] && [ -n "$parts" ]; then
        printf '%s\\n' $parts | xargs -n 40 rm -f 2>/dev/null
      fi
      overall=1; continue'''

MARK = "自愈补丁（2026-09-18 夜间）"

src = io.open(P, encoding="utf-8").read()

if MARK in src:
    print("[skip] 补丁已存在，dl_ena.sh 无需再改")
    sys.exit(0)

if OLD not in src:
    print("[FAIL] 未找到锚点 OLD —— 脚本可能被改过，请人工核对 dl_ena.sh 第 254-258 行")
    sys.exit(2)

io.open(P, "w", encoding="utf-8", newline="\n").write(src.replace(OLD, NEW, 1))
print("[ok] 补丁已写入 dl_ena.sh（bad 分支清理 .partN）")
