# -*- coding: utf-8 -*-
"""细读审稿后的问题修复（2026-10-03）。

分两类：
  [硬] 与数据不符 / 审稿人一查就发现
  [文] 措辞、时态、重复、元信息过时
每条都写明依据，便于复核。
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
        log.append("  [%d] %s" % (n, note))
    elif n == 0:
        log.append("  [!! 未命中] %s" % note)
    s = s2
    return n


print("=" * 68)
print("审稿修复")
print("=" * 68)

# ============ [硬] 1. Table 2 的 P4 行：Rice/Hybrid 两列对调 ============
# 依据 gea_input_P.tsv：P4 = 14 C + 1 R + 0 H
#   （全队列因此是 C147 / R66 / H1；原表写成 14C+0R+1H 会让 H 变成 2）
sub(r"\| P4 \| 15 \| 14 \| 0 \| 1 \| molecular \|",
    "| P4 | 15 | 14 | 1 | 0 | molecular |",
    "[硬] Table 2 的 P4 行 Rice/Hybrid 对调 → 14C+1R+0H")

# ============ [硬] 2. 547 → 550（两处）============
# 依据 crossregion_genes.tsv：n_region>=3 恰好 550（=376+134+40）
sub(r"genes shared across ≥3 panels \(547 genes\)",
    "genes shared across ≥3 panels (550 genes)",
    "[硬] §2.12 的 547 → 550")
sub(r"the shared gene set \(547 genes\)",
    "the shared gene set (550 genes)",
    "[硬] §3.10 的 547 → 550")

# ============ [硬] 3. 位点数 16,230,602 vs 实际进入检验的 16,230,598 ============
# 依据 gea_rda.py L95-97：去掉方差 <= 1e-6 的单态位点，恰为 4 个
sub(r"the full site set was processed in a streaming block fashion \(the dense genotype matrix for all 16\.2 M sites would require 84 GB\)\. All 16,230,602 sites were used; the 200,000-site thinned version returned an identical R² \(2\.30%\)\.",
    "the full site set was processed in a streaming block fashion (the dense genotype matrix for all 16.2 M sites would require 84 GB). All **16,230,602** variable sites were taken forward; after removing four monomorphic sites (expected dosage variance ≤ 1 × 10⁻⁶), **16,230,598** sites entered the test, matching the *m* used for BH control in §2.9. The 200,000-site thinned version returned an identical R² (2.30%).",
    "[硬] §2.7 补明 4 个单态位点被剔除，解释 602 与 598 的差异")

# ============ [硬] 4. §4.6 第 3 条时态自相矛盾 ============
# 原文先说 "has been prepared"（还没做），后文却说结果如何（已经做完）
sub(r"A sensitivity re-analysis excluding all three has been prepared \(`run_sens_excl3\.sh`\); exclusion reduces",
    "A sensitivity re-analysis excluding all three has been run (§3.9); exclusion reduces",
    "[硬] §4.6-3 时态矛盾 has been prepared → has been run")

# ============ [文] 5. polygenic 重复 ============
sub(r"the expected architecture of a polygenic, highly polygenic trait",
    "the expected architecture of a highly polygenic trait",
    "[文] §4.1 'polygenic, highly polygenic' 重复用词")

# ============ [文] 6. proved 用词过强 ============
sub(r"Because candidate genes proved substantially longer than background genes",
    "Because candidate genes are substantially longer than background genes",
    "[文] §2.12 'proved' → 'are'（统计差异不等于证明）")

# ============ [文] 7. 面板指代与 P1 改名决策矛盾 ============
sub(r"tested for genotype–environment association within the United States study panel \(n = 143\)",
    "tested for genotype–environment association within the P1 study panel (n = 143)",
    "[文] Abstract 'United States study panel' → P1")
sub(r"We restrict formal genotype–environment association testing to the United States accession",
    "We restrict formal genotype–environment association testing to the P1 accession",
    "[文] Introduction 'United States accession' → P1")

# ============ [文] 8. 元信息过时 ============
sub(r"\*\*Version:\*\* v1 draft, 2026-09-24",
    "**Version:** v2 draft, 2026-09-25",
    "[文] Version 标注 v1 → v2")
sub(r"\*\*Citation style:\*\* author–year \(Harvard\)\. In-text citations are marked `\[CITE: …\]` — see \"Reference scaffolding\" at the end\.",
    "**Citation style:** author–year (Harvard). All in-text citations are resolved; **three** placeholders remain — the repository DOI, author contributions and funding (see \"Numbers to verify before submission\" at the end).",
    "[文] 引用说明过时（23 处已补全，只剩 3 处待填）")

io.open(DST, "w", encoding="utf-8", newline="\n").write(s)

print("已应用：")
for l in log:
    print(l)

# ============ 复核 ============
print("\n" + "=" * 68)
print("复核")
print("=" * 68)
print("残留 547          :", s.count("547"))
print("残留 'United States study/panel':", len(re.findall(r"United States (?:study |accession|panel)", s)))
print("残留 'proved'     :", s.count("proved"))
print("残留 'has been prepared':", s.count("has been prepared"))
print("Table 2 P4 行     :", re.search(r"\| P4 \| 15 \|[^\n]*", s).group(0))
print("550 出现次数      :", s.count("550"))
m = re.search(r"[^.]*16,230,598[^.]*\.", s)
print("\n位点说明:\n   ", (m.group(0)[:300] if m else "未找到"))
