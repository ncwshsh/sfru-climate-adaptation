# -*- coding: utf-8 -*-
"""Numbers to verify 第 5 条：LFMM-type 方法措辞统一 + md 下标记号排版修复。

背景（2026-10-02）
------------------
① 方法措辞：官方 lfmm2 二进制装不上（无 conda 包、仓库不可用），我们用
   「线性模型 + PCA 估潜因子 + 气候系数联合 F 检验」替代，已在 §2.8 与
   §4.6 item 4 说明该偏差。稿子定调：一律称 **LFMM-type**，*绝不* 简称
   LFMM 或 LFMM2（后者会被读成官方实现）。

② 顺带发现的排版 bug：原稿用 `|*z*|_RDA`、`*p*_LFMM`、`*m*_eff` 这类
   `_` 下标写法，但 md2html 转换器**不支持**，实测：
     - md  : `|*z*|_RDA and −log₁₀(*p*_LFMM)`
     - html: `|<em>z</em>|_RDA and −log₁₀(*p*_LFMM)`   ← `*p*` 没变斜体
   根因：`_RDA … *p*_` 被 markdown 当成一对下划线强调，把中间的 `*p*` 吞了。
   结果 Word 里直接显示原始标记 `*p*_LFMM`，审稿人可见。
   对照：Table 3 的 `*p* (RDA)` / `*p* (LFMM-type)` 渲染正常 ⇒ 改用括号形式。

本脚本只做这三件事，改完打印逐条供人工复核。
"""
import io, re, sys

SRC = sys.argv[1]
DST = sys.argv[2] if len(sys.argv) > 2 else SRC

s = io.open(SRC, encoding="utf-8").read()
log = []


def sub(pat, repl, note, flags=0):
    global s
    s2, n = re.subn(pat, repl, s, flags=flags)
    if n:
        log.append(f"  [{n}] {note}")
    s = s2
    return n


# ============ 第 5 条正文（先做，避免后续规则误伤）============
sub(
    r"5\. \*\*LFMM-type method wording\.\*\* Confirm that all instances read \"LFMM-type\" "
    r"and that §4\.6 item 4 is retained, given the official binary was unavailable\.",
    "5. ~~LFMM-type method wording.~~ **RESOLVED 2026-10-02.** "
    "Every mention of the second method now reads **\"LFMM-type\"** and never bare \"LFMM\" or \"LFMM2\" "
    "(the three surviving `LFMM2` occurrences refer specifically to the *official algorithm and its "
    "unavailable binary*, which is the correct usage). Specifically: "
    "(i) the §2.8 heading and text, the Abstract, §1 and §3.6 all read \"LFMM-type\"; "
    "(ii) the §3.7 in-text table column now reads `*p* (LFMM-type)`, matching Table 3; "
    "(iii) in §3.6 and in the Fig. S2 legend the two statistics are written in explicit parenthetical "
    "form — `|*z*| (RDA)` and `*p* (LFMM-type)` — replacing the `_`-subscript notation "
    "(`|*z*|_RDA`, `*p*_LFMM-type`) that the Word conversion did not render, so the manuscript no longer "
    "shows raw markup; the same fix was applied to `*m*_eff`; "
    "(iv) the **Fig. S2 y-axis label** was changed from an unlabelled `single-SNP F test` to "
    "`LFMM-type F test`, so the figure now names the method explicitly. "
    "§4.6 item 4 (\"The LFMM-type test is not the official LFMM2 implementation\") is **retained verbatim**. "
    "The only substantive deviation from the published algorithm — latent factors estimated by PCA rather "
    "than by joint EM — is stated in §2.8 and §4.6.",
    "第5条 -> RESOLVED")

# ============ ① 方法措辞：裸 LFMM -> LFMM-type ============
# §3.6 定性表述
sub(r"the LFMM statistic", "the LFMM-type statistic",
    "§3.6: the LFMM statistic -> the LFMM-type statistic")

# §3.7 正文内联表列名，对齐 Table 3
sub(r"\*p\* \(LFMM\)", "*p* (LFMM-type)",
    "§3.7 内联表列名 -> *p* (LFMM-type)")

# ============ ② 排版修复：`_` 下标 -> 括号形式 ============
# 注意：此刻文本仍是回滚态 `(*p*_LFMM)`（尚未加 -type），故 old 串按现状写，
# 并在 new 串里一并补上 -type 后缀。
# §3.6 正文（一句内同时含 _RDA 与 _LFMM）
sub(r"between \|\*z\*\|_RDA and −log₁₀\(\*p\*_LFMM\)",
    "between |*z*| (RDA) and −log₁₀ *p* (LFMM-type)",
    "§3.6: |*z*|_RDA / *p*_LFMM -> 括号形式 + LFMM-type")

# Fig S2 图注
sub(r"\|\*z\*\|_RDA vs −log₁₀\(\*p\*_LFMM\)",
    "|*z*| (RDA) vs −log₁₀ *p* (LFMM-type)",
    "Fig S2 图注: 同上")

# *m*_eff（2 处）
sub(r"\(\*m\*_eff = 7,643\)", "(effective *m* = 7,643)",
    "*m*_eff -> (effective *m*)")

io.open(DST, "w", encoding="utf-8", newline="\n").write(s)

print(f"写入 {DST}")
print(f"共 {len(log)} 类替换：")
for l in log:
    print(l)

# ============ 复核 ============
print("\n=== 复核 1：LFMM 形态统计 ===")
from collections import Counter
c = Counter(m.group(0) for m in re.finditer(r"LFMM[\w\-]*", s))
for k, v in sorted(c.items()):
    print(f"  {k:<16} x{v}{'   <<<< 裸 LFMM' if k == 'LFMM' else ''}")

print("\n=== 复核 2：失效下标残留（应为 0，excluding 说明文本）===")
for pat in [r"\|_RDA", r"_LFMM-type", r"_eff"]:
    hits = [m for m in re.finditer(pat, s)]
    # 说明文本里的反引号引用不算
    real = [m for m in hits if "`" not in s[max(0, m.start()-3):m.start()+3]]
    print(f"  {pat:<16} 总 {len(hits)}  非代码引用 {len(real)}")
    for m in real:
        print("     !", s[max(0, m.start()-70):m.end()+30].replace("\n", " "))

print("\n=== 复核 3：LFMM2 逐处语境（应均为『官方算法/二进制』）===")
for i, m in enumerate(re.finditer(r"LFMM2", s), 1):
    print(f"  {i}.", s[max(0, m.start()-95):m.end()+95].replace("\n", " "))

print("\n=== 复核 4：§3.6 与 Fig S2 图注最终形态 ===")
for key in ["between |*z*|", "Concordance between the two association methods"]:
    i = s.find(key)
    if i >= 0:
        print("  •", s[i:i+180].replace("\n", " "))
