# -*- coding: utf-8 -*-
"""按 Molecular Ecology 官方 Author Guidelines 调整稿件（2026-10-03）。

ME 官方要求（onlinelibrary.wiley.com/page/journal/1365294x/homepage/guide.htm）：
  · Abstract ≤ 250 words
  · Keywords: 4–6
  · Original Article ≤ 8000 words excluding references
  · 顺序：Title Page / Abstract / Introduction / Materials and Methods / Results /
          Discussion / Acknowledgements / References / Data Accessibility /
          Author Contributions / Tables and Figures
  · 投稿系统：mc.manuscriptcentral.com/mec (ScholarOne)
  · Cover Letter 须说明与 Aims & Scope 的契合度
注意：ME 也写明「技术方法/计算机程序/基因组资源开发」应转 MER ——
本稿主体是实证研究 + 分析方法诊断，属 ME 的
「molecular adaptation and environmental genomics」范围，故留在 ME。
"""
import io, re, sys

SRC = sys.argv[1]
DST = sys.argv[2] if len(sys.argv) > 2 else SRC
s = io.open(SRC, encoding="utf-8").read()
log = []


def sub(pat, repl, note, flags=0):
    global s
    s2, n = re.subn(pat, repl, s, flags=flags)
    log.append("  [%d] %s" % (n, note))
    s = s2
    return n


print("=" * 66)
print("按 Molecular Ecology 要求调整")
print("=" * 66)

# ---------- 1. Abstract：366 → ≤250 词 ----------
# 改写原则：① 以「发现」为主线、方法论警示降为 "we further show"（避免被判定为纯技术方法稿）
#          ② 保留全部关键数字（R²/λ/69/三模块 p/550/2.42×/ρ）
NEW_AB = """## Abstract

Publicly available resequencing data are increasingly used to test adaptive responses to climate, but reference bias, unequal depth and host-strain structure can each generate signals that mimic adaptation. Using 214 *Spodoptera frugiperda* from 12 countries (six study accessions) retained as genotype likelihoods at 16,230,602 sites across all 31 nuclear chromosomes, we confined formal testing to the one panel (n = 143) spanning a 22.9° latitude gradient (annual mean temperature 6.2–24.4 °C; *r* = −0.896 with latitude), fitting host strain and genomic axes PC2–PC4 as conditioning variables. Partial redundancy analysis attributed 2.30% of genetic variation to climate (999 permutations, *p* = 0.001; λ = 0.9485), with only 69 sites surviving strict Benjamini–Hochberg control — a sparse, polygenic signal rather than a few large-effect loci. Testing three *a priori* functional modules instead detected enrichment of **heat-shock proteins** (*p* = 0.0010) and **oxidative stress** (*p* = 0.0005), each reproduced by an independent LFMM-type single-locus test, whereas **diapause/photoperiod** was null under both (*p* = 1.0000, 0.9955). Candidate gene sets were strongly shared across panels (2.3–3.0-fold enrichment; 550 genes in ≥3), yet the enriched modules differed, indicating a shared gene inventory recruited through different pathways. We further show that counting-based gene enrichment is distorted by gene-length bias (candidates 2.42× longer than background, *p* = 4.3 × 10⁻¹⁵⁴) whereas module-level enrichment is not (ρ = +0.006). Climate adaptation in this species is therefore polygenic and largely non-parallel."""
sub(r"## Abstract\n\n.*?\n\n\*\*Keywords:\*\*",
   NEW_AB + "\n\n**Keywords:**",
   "Abstract 重写为 ME 版（≤250 词）", flags=re.S)

# ---------- 2. Keywords：8 → 6 ----------
sub(r"landscape genomics, genotype–environment association, redundancy analysis, invasive species, heat-shock proteins, oxidative stress, polygenic adaptation, reference bias",
   "landscape genomics, genotype–environment association, reference bias, invasive species, polygenic adaptation, heat-shock proteins",
   "Keywords 8 → 6（ME 要求 4–6）")

# ---------- 3. 章节顺序对齐 ME ----------
# ME: ... Discussion | Acknowledgements | Data Accessibility | Author Contributions | References | Tables and Figures
# 现稿: ... Discussion | Data accessibility | Author contributions | Acknowledgements | Figure legends | Tables | References
i_da = s.find("## Data accessibility")
i_ac = s.find("## Author contributions")
i_ack = s.find("## Acknowledgements")
i_fl = s.find("## Figure legends")
i_tab = s.find("## Tables\n")
i_ref = s.find("## References")
i_ntv = s.find("## Numbers to verify")
if min(i_da, i_ac, i_ack, i_fl, i_tab, i_ref) > 0:
    seg_ack = s[i_ack:i_fl]
    seg_da = s[i_da:i_ac]
    seg_ac = s[i_ac:i_ack]
    seg_fl = s[i_fl:i_ref]            # Figure legends + Tables（从 Figure legends 起，不是从 Tables 起）
    seg_ref = s[i_ref:i_ntv]
    s = (s[:i_da] + seg_ack + seg_da + seg_ac + seg_ref + seg_fl
         + s[i_ntv:]) if i_ntv > 0 else (s[:i_da] + seg_ack + seg_da + seg_ac + seg_ref + seg_fl)
    log.append("  [1] 章节顺序对齐 ME（Acknowledgements → Data accessibility → Author contributions → References → Figures/Tables）")

# ---------- 4. 卷首 Target journal 更新 ----------
sub(r"\*\*Target journal:\*\* \*Molecular Ecology\* \(alternatives: \*Genome Biology and Evolution\*, \*Molecular Biology and Evolution\*\)",
    "**Target journal:** *Molecular Ecology* (Wiley; submission via ScholarOne — mc.manuscriptcentral.com/mec)",
    "卷首 Target journal 更新为 ME + 投稿系统")

io.open(DST, "w", encoding="utf-8", newline="\n").write(s)
print("已应用：")
for l in log:
    print(l)

# ---------- 复核 ----------
print("\n" + "=" * 66)
print("复核（对照 ME 官方要求）")
print("=" * 66)
i = s.find("## Abstract"); j = s.find("**Keywords:**")
ab = s[i:j]
aw = len(re.sub(r"\*\*|\*", " ", ab).split())
print("  Abstract      : %d 词   [≤250]  %s" % (aw, "✅" if aw <= 250 else "❌ 超 %d" % (aw - 250)))
kw = s[j + 13:s.find("## 1. Introduction")].strip()
nk = len([k for k in kw.split(",") if k.strip()])
print("  Keywords      : %d 个   [4–6]   %s" % (nk, "✅" if 4 <= nk <= 6 else "❌"))
b0 = s.find("## 1. Introduction"); b1 = s.find("## References")
bw = len(re.sub(r"\*\*|\*|\^|\||#", " ", s[b0:b1]).split())
print("  正文          : %d 词   [≤8000] %s" % (bw, "✅" if bw <= 8000 else "❌"))
print("  关键数字仍在  :", all(k in s for k in ["2.30%", "0.9485", "69 sites", "0.0010",
                                          "0.0005", "1.0000", "0.9955", "550", "2.42", "+0.006"]))
print("\n  结构顺序:")
for m in re.finditer(r"^## .*$", s, re.M):
    print("     ", m.group(0))
