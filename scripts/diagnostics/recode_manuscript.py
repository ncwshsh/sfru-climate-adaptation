# -*- coding: utf-8 -*-
"""路线 2 第二步：把正文的面板代号改成中性 P1–P6。

关键区分（这是本脚本存在的唯一理由）：
  ① 「面板代号」必须改：`US panel` / `BR-C` / `AF-C` / `the AF panel` / `(US, FL, BR, CN, AF, AM)`
  ② 「真实地理」必须留：`continental USA` / `Florida, USA` / `sampled in Brazil` /
     `China`（作为国家名）/ `Kenya` / `Argentina` …
  所以**绝不能**全局 \bUS\b -> P1，那会把 `continental USA` 变成 `continental P1A`。

做法：按「后缀/前缀语境」分类替换，全部走显式规则，改完逐条打印供人工复核。
"""
import io, re, sys

SRC = sys.argv[1]
DST = sys.argv[2] if len(sys.argv) > 2 else SRC

M = {"US": "P1", "BR": "P2", "AF": "P3", "AM": "P4", "CN": "P5", "FL": "P6"}

s = io.open(SRC, encoding="utf-8").read()
log = []


def sub(pat, repl, note, flags=0):
    global s
    s2, n = re.subn(pat, repl, s, flags=flags)
    if n:
        log.append(f"  [{n:>2}] {note}")
    s = s2
    return n


# ---------- 1. 面板-株系记号 X-C / X-R / X-H（最安全，先做）----------
for old, new in M.items():
    sub(rf"\b{old}-([CRH])\b", rf"{new}-\1", f"{old}-C/R/H  ->  {new}-C/R/H")

# ---------- 2. 明确带「面板」词的语境 ----------
# "the US panel" / "US panel" / "the AF and AM panels" / "US (n = 143)"
for old, new in M.items():
    sub(rf"\b{old}\s+panel\b", rf"{new} panel", f"{old} panel  ->  {new} panel")
    sub(rf"\b{old}\s+panels\b", rf"{new} panels", f"{old} panels  ->  {new} panels")

# ---------- 3. 各面板在 §3.1 的 "(CODE (n = N))" 枚举形式 ----------
for old, new in M.items():
    sub(rf"\*\*{old}\*\*\s*\(n", rf"**{new}** (n", f"**{old}** (n  ->  **{new}** (n")
    sub(rf"\*\*{old}\*\*", rf"**{new}**", f"**{old}**  ->  **{new}**")

# ---------- 4. 「the AF and AM panels」等连写 ----------
sub(r"\b(AF|AM|US|BR|CN|FL)\s+and\s+(AF|AM|US|BR|CN|FL)\s+panels\b",
    lambda m: f"{M[m.group(1)]} and {M[m.group(2)]} panels", "X and Y panels")

# ---------- 5. 面板作为主语/宾语的裸用（限定在明确的技术语境）----------
# 这些是稿件里明确以"面板"身份出现、但省略了 panel 一词的位置
explicit = [
    (r"\bthe US panel\b", "P1"),
    (r"\bthe CN panel\b", "P5"),
    (r"\bthe BR panel\b", "P2"),
    (r"\bthe AF panel\b", "P3"),
    (r"\bthe AM panel\b", "P4"),
]
# 已由第 2 步覆盖，此处不再重复

# ---------- 6. 表格/图注里的面板代号（独立成词、且位于|包裹或逗号列表）----------
# 表格行首 "| US-C |" 已在第 1 步处理。
# §3.9 表的 "US-C" "BR-C" 等已处理。
# Fig.3 提到的 "(Fig. 3; Table 2). The source-region panel (FL) was mixed"
sub(r"source-region panel \(FL\)", "source-region panel (P6)",
    "source-region panel (FL)")

# ---------- 7. §2.1 术语块与枚举 ----------
sub(r"\(US, FL, BR, CN, AF, AM\)", "(P1, P2, P3, P4, P5, P6)",
    "§2.1 枚举 (US, FL, ...) -> (P1, ...)")

# ---------- 8. 坐标精度句 ----------
sub(r"Coordinates for the US, FL and BR panels", "Coordinates for the P1, P6 and P2 panels",
    "坐标精度句（面板名）")
sub(r"\(the AF and AM panels\) are country centroids", "(the P3 and P4 panels) are country centroids",
    "国质心面板名")

# ---------- 9. 低比对率样本列举里的面板代号 ----------
sub(r"60\.19%, BR; SRR12044624, 68\.87%, AM; SRR9289279, 69\.87%, BR",
    "60.19%, P2; SRR12044624, 68.87%, P4; SRR9289279, 69.87%, P2",
    "残留样本面板代号")

# ---------- 10. 株系组成枚举 ----------
sub(r"corn-strain: BR 24/24 C, AF 16/16 C, CN 10/10 C, and AM 14/1",
    "corn-strain: P2 24/24 C, P3 16/16 C, P5 10/10 C, and P4 14/1",
    "株系组成枚举")

# ---------- 11. 面板集合列举（§4.6 / §4.7）----------
sub(r"excluding them reduces the BR-C panel from 24 to 22 and the AM-C panel from 14 to 13",
    "excluding them reduces the P2-C panel from 24 to 22 and the P4-C panel from 14 to 13",
    "剔除影响（面板-C）")

# ---------- 12. 无 power 面板列表 ----------
sub(r"The CN \(\*n\* = 10\), AF \(\*n\* = 16\) and AM \(\*n\* = 14–15\) panels",
    "The P5 (*n* = 10), P3 (*n* = 16) and P4 (*n* = 14–15) panels",
    "低功效面板列表")

# ---------- 13. 全队列比对率排序句 ----------
sub(r"highest in the AF \(97\.83% mean\), US \(96\.45%\) and AM \(93\.59%\) panels",
    "highest in the P3 (97.83% mean), P1 (96.45%) and P4 (93.59%) panels",
    "比对率排序句")

# ---------- 14. §3.1 表下段的 within-BR / within-P1 ----------
sub(r"within-BR correlations", "within-P2 correlations", "within-BR -> within-P2")

# ---------- 15. §4.4 的 "the AF and AM multi-country panels" ----------
sub(r"the AF and AM multi-country panels", "the P3 and P4 multi-country panels",
    "多国面板（§4.4）")

# ---------- 16. "AM-C individual from Kenya" ----------
sub(r"an AM-C individual from Kenya", "a P4-C individual from Kenya", "AM-C 个体")

# ---------- 17. 残留 §3.1 表内 BR 行 ----------
sub(r"Within BR panel \(n = 30\)", "Within P2 panel (n = 30)", "§3.1 表 BR 行")

# ---------- 18. 正文其它 "US 个体" ----------
sub(r"all 143 US individuals", "all 143 P1 individuals", "143 US individuals")
sub(r"the 142 annotated US individuals", "the 142 annotated P1 individuals", "142 US individuals")
sub(r"across the annotated US individuals", "across the annotated P1 individuals", "annotated US individuals")
sub(r"approximately eight US individuals", "approximately eight P1 individuals", "eight US individuals")

# ================= 19–33：补漏（残余 13 处）=================
# 原则：只改「以面板身份出现」的裸代号；保留 continental USA / Florida, USA /
#       sampled in Brazil / Brazil（国家名）/ Kenya / Argentina 等真实地理。

# --- 19. §3.1 表下段：面板名枚举 ---
sub(r"Coordinates for the US, FL and BR panels",
    "Coordinates for the P1, P6 and P2 panels", "坐标精度句（面板名，补）")
sub(r"(31 \(the AF and AM panels\) are country centroids|\(the AF and AM panels\) are country centroids)",
    lambda m: m.group(0).replace("AF", "P3").replace("AM", "P4"), "国质心 31（§3.1 表下段）")
sub(r"and for the AF and AM panels country centroids",
    "and for the P3 and P4 panels country centroids", "国质心（§2.5 方法段）")

# --- 20. 全队列比对率排序句（残缺版本：上一轮只匹配了带 mean 的长串）---
sub(r"highest in the AF \(97\.83% mean\), US \(96\.45%\) and AM \(93\.59%\) panels",
    "highest in the P3 (97.83% mean), P1 (96.45%) and P4 (93.59%) panels", "比对率排序（补）")
sub(r"intermediate in FL \(91\.33%\) and CN \(86\.36%\), and lowest in BR \(84\.25%\)",
    "intermediate in P6 (91.33%) and P5 (86.36%), and lowest in P2 (84.25%)", "比对率排序（中低段）")

# --- 21. 中位深度句：CN panel ---
sub(r"except for the CN panel \(12\.2×\)", "except for the P5 panel (12.2×)", "中位深度 CN 面板")

# --- 22. 剔除说明里的 "belong to the BR panel" / "the next-lowest BR library" ---
sub(r"All six belong to the BR panel", "All six belong to the P2 panel", "剔除：belong to BR panel")
sub(r"the next-lowest BR library maps at 60\.2%", "the next-lowest P2 library maps at 60.2%",
    "剔除：next-lowest BR library")
sub(r"\(§2\.1; all BR, mapping rate 36–52%\)", "(§2.1; all P2, mapping rate 36–52%)",
    "§3.1 表注 all BR")

# --- 23. 敏感性分析增补段（§3.9/§4.6 的重复叙述）---
sub(r"60\.19%, BR; SRR12044624, 68\.87%, AM; SRR9289279, 69\.87%, BR",
    "60.19%, P2; SRR12044624, 68.87%, P4; SRR9289279, 69.87%, P2", "残留样本列表（重复处）")
sub(r"reduces the corn-strain BR panel from 24 to 22 individuals and the AM panel from 14 to 13",
    "reduces the corn-strain P2 panel from 24 to 22 individuals and the P4 panel from 14 to 13",
    "敏感性：BR/AM panel 缩减")
sub(r"leaving the US \(80\), AF \(16\) and CN \(10\) panels unchanged",
    "leaving the P1 (80), P3 (16) and P5 (10) panels unchanged", "敏感性：unchanged 面板")

# --- 24. within-BR（残余两处：§3.1 表下段 / Numbers-to-verify 第 3 条）---
sub(r"the within-BR correlations become", "the within-P2 correlations become",
    "within-BR correlations（补）")
sub(r"the negative within-BR association was carried", "the negative within-P2 association was carried",
    "negative within-BR association")
sub(r"The within-BR row was likewise labelled", "The within-P2 row was likewise labelled",
    "within-BR row")

# --- 25. "within the US panel"（§3.1 诊断句、§4.5）---
sub(r"within the US panel", "within the P1 panel", "within the US panel")
sub(r"restricting formal association testing to the US panel",
    "restricting formal association testing to the P1 panel", "restricting ... to the US panel")
sub(r"within the US panel alone", "within the P1 panel alone", "Fig.7 图注 within US panel alone")

# --- 26. §3.9 cross-panel 矩阵句（US-C/AM-C/BR-C/AF-C/CN-C 已在规则 1 改；
#         但 "US-C ∩ BR-C" 等被 \b 保护完好，本处补 "the US-C panel" 类）---
sub(r"the US-C panel was enriched", "the P1-C panel was enriched", "§3.9 US-C panel enriched")
sub(r"oxidative stress in both the US-C and AM-C panels",
    "oxidative stress in both the P1-C and P4-C panels", "模块模式 US-C/AM-C")
sub(r"US-C oxidative stress \(0\.0005\), AF-C HSP \(0\.0185\) and CN-C diapause \(0\.0005\)",
    "P1-C oxidative stress (0.0005), P3-C HSP (0.0185) and P5-C diapause (0.0005)",
    "敏感性：三面板复现")
sub(r"the AM panel loses one individual", "the P4 panel loses one individual", "AM panel loses one")

# --- 27. §4.6 单一非稳健结果：AM panel / AM-C diapause ---
sub(r"a nominal diapause signal in the AM panel", "a nominal diapause signal in the P4 panel",
    "§4.6 AM panel diapause")
sub(r"the nominal AM-C diapause enrichment", "the nominal P4-C diapause enrichment",
    "§4.6 AM-C diapause enrichment")
sub(r"\*\*the design cannot resolve\. In the AF and AM panels",
    "**the design cannot resolve. In the P3 and P4 panels", "§4.6 多国面板 caveat")
sub(r"the \"climate\" summarising an AM-C individual",
    "the \"climate\" summarising a P4-C individual", "§4.6 AM-C individual 引号版")

# --- 28. §3.9 低功效/样本量句 ---
sub(r"Small panels \(CN, \*n\* = 10\)", "Small panels (P5, *n* = 10)", "低功效 CN 面板")
sub(r"they could in principle affect the composition of the BR-C candidate gene set",
    "they could in principle affect the composition of the P2-C candidate gene set", "§3.9 BR-C gene set")

# --- 29. §2.1 术语块 + 首句面板枚举（**US** (n = 143) 等已在规则 3 改；
#         但首句 "**US** (n = 143; 137 from the continental USA plus 6 ...)" 的 US 被
#         规则 3 的 `**US** (n` 命中，已改为 **P1**；continental USA 保留 ✅）---
sub(r"the six codes \(US, FL, BR, CN, AF, AM\)", "the six codes (P1–P6)",
    "§2.1 术语块代号枚举")

# --- 30. Numbers to verify 第 4 条自身 -> RESOLVED ---
sub(r"4\. \*\*AF/AM panel naming\.\*\*",
    "4. ~~AF/AM panel naming.~~ **RESOLVED 2026-09-25 by relabelling.**", "第4条：标记 RESOLVED")
sub(r"Figure labels use AF and AM, which read as continental but are multi-country study accessions \(eight and five countries respectively\)\. Either retain the codes with the explicit disclaimer now in §2\.1, or relabel both the figures and the text\.",
    "The six panels are now labelled with **neutral study-accession codes P1–P6** throughout the manuscript, the figures and the supplementary tables, removing the geographic reading that the old codes invited. The mapping is fixed and documented in `report/panel_map.tsv`: **P1** = the n = 143 accession (137 continental USA + 6 Puerto Rico), **P2** = the n = 24 Brazilian accession, **P3** = the n = 16 eight-country accession, **P4** = the n = 15 five-country accession, **P5** = the n = 10 Chinese accession, **P6** = the n = 6 Florida accession. Codes were assigned in descending order of analysed sample size. Panel colours were kept identical across the two codings, so the regenerated figures differ only in labels and axis annotations. All real-geography statements (e.g. \"the continental USA\", \"sampled in Brazil\", Kenya, Argentina) are retained verbatim. §2.1 now states that the codes denote public study accessions and points to the mapping table.",
    "第4条：正文替换")

# ================= 34–40：二次补漏（前序规则互相抢文本导致的失配）=================
# 教训：规则之间会互相改写对方要匹配的串。必须按「当前实际文本」写。
# 下面这几条故意放在最末，用最终态文本匹配。

sub(r"Coordinates for the US, FL and P2 panels",
    "Coordinates for the P1, P6 and P2 panels", "坐标精度句（终态匹配）")
sub(r"and for the AF and P4 panels country centroids",
    "and for the P3 and P4 panels country centroids", "国质心（终态匹配）")
sub(r"and 31 \(the AF and P4 panels\) are country centroids",
    "and 31 (the P3 and P4 panels) are country centroids", "国质心 31（终态匹配）")
sub(r"highest in the AF \(97\.83% mean\), US \(96\.45%\) and AM \(93\.59%\) panels",
    "highest in the P3 (97.83% mean), P1 (96.45%) and P4 (93.59%) panels", "比对率（终态匹配）")
sub(r"intermediate in FL \(91\.33%\) and CN \(86\.36%\), and lowest in BR \(84\.25%",
    "intermediate in P6 (91.33%) and P5 (86.36%), and lowest in P2 (84.25%", "比对率中低段（终态匹配）")
sub(r"cannot resolve\. In the AF and P4 panels",
    "cannot resolve. In the P3 and P4 panels", "§4.6 caveat（终态匹配）")

# ================= 41–42：§2.1 首句枚举重排 + 术语块补中性代号理由 =================
# 首句枚举按原顺序（US,FL,BR,CN,AF,AM）改码后变成 P1,P6,P2,P5,P3,P4，读起来乱，
# 需重排为 P1→P6 并显式说明排序依据。
sub(r"corresponding to distinct public BioProjects: \*\*P1\*\* \(n = 143; 137 from the continental USA plus 6 from Puerto Rico\), \*\*P6\*\* \(n = 6; Florida, USA\), \*\*P2\*\* \(n = 24; Brazil\), \*\*P5\*\* \(n = 10; China\), \*\*P3\*\* \(n = 16\) and \*\*P4\*\* \(n = 15\)\.",
    "corresponding to distinct public BioProjects, labelled **P1**–**P6** in descending order of analysed sample size: **P1** (n = 143; 137 from the continental USA plus 6 from Puerto Rico), **P2** (n = 24; Brazil), **P3** (n = 16), **P4** (n = 15), **P5** (n = 10; China) and **P6** (n = 6; Florida, USA).",
    "§2.1 首句枚举重排")

sub(r"> \*\*Terminology\.\*\* The six codes \(P1, P2, P3, P4, P5, P6\) denote \*public study accessions\*, retained for consistency with the figures; \*\*they are not geographic labels\*\*\. In particular,",
    "> **Terminology.** Panels are labelled with neutral study-accession codes **P1**–**P6**, deliberately chosen so that the labels carry no geographic implication (the mapping, together with coordinate precision and country composition, is tabulated in `report/panel_map.tsv`). The codes denote *public study accessions* and are retained for consistency with the figures; **they are not geographic labels**. In particular,",
    "§2.1 术语块（中性代号理由）")

# ================= 43：图注漏改 =================
sub(r"Strain assignments for panels other than US are molecular predictions",
    "Strain assignments for panels other than P1 are molecular predictions",
    "Fig.3 图注 panels other than US")

# ================= 44：§4.5 段末 =================
sub(r"the structure that exists only for the US and P2 panels here",
    "the structure that exists only for the P1 and P2 panels here", "§4.5 段末 US and P2 panels")

# ================= 45–46：Table 1 / Table 2 的「Panel」列（行首 | CODE |）=================
# 关键：只用行首 `| CODE |` 锚定，绝不碰第二列（Countries represented）里的真实国名 USA。
# Table 1: | US | USA, Puerto Rico | ...   → 改第 1 列
# Table 2: | US | 143 | 80 | ...           → 改第 1 列
for old, new in M.items():
    sub(rf"^\| {old} \|", rf"| {new} |", f"表格行首 | {old} |  ->  | {new} |", flags=re.M)

# ================= 47：Numbers to verify 第 3 条内的 within-BR / 第 4 条标题 =================
sub(r"The within-BR negative association \(−0\.223\) is carried entirely",
    "The within-P2 negative association (−0.223) is carried entirely", "NTV 第3条 within-BR Note")
sub(r"4\. \*\*AF/P4 panel naming\.\*\*", "4. ~~AF/AM panel naming.~~ **RESOLVED 2026-09-25 by relabelling.**",
    "NTV 第4条标题（补）")

# ================= 48：Table 1 / Table 2 行序重排为 P1→P6 =================
# 改码后行序变成 P1,P6,P2,P5,P3,P4（沿袭旧 US,FL,BR,CN,AF,AM），读起来乱。
# 按 P1→P6 重排。只动「以 | CODE | 开头的连续数据行块」，不动表头/分隔线/总行。
import re as _re
def _reorder_table(block_marker, order):
    """只重排「单个表格」的数据行。★教训：之前用固定 4000 字符窗口会把下一个
    表格的行也圈进来，导致 rows 字典被后一个表同名键覆盖、整表内容串位。
    改为：从 marker 起，扫到第一个空行（表格结束）为止。"""
    global s
    i = s.find(block_marker)
    if i < 0:
        return 0
    # marker 行本身是 "**Table N** ..."，其后是空行，再后才是表格块。
    # 表格块 = 空行之后 到 再下一个空行。
    a = s.find("\n\n", i)
    if a < 0:
        return 0
    a += 2                                    # 跳过空行，指向表头
    b = s.find("\n\n", a)
    if b < 0:
        b = len(s)
    seg = s[a:b]
    lines = seg.split("\n")
    idxs = [k for k, l in enumerate(lines) if _re.match(r"^\| (P\d) \|", l)]
    if len(idxs) != len(order):
        return 0
    rows = {_re.match(r"^\| (P\d) \|", lines[k]).group(1): lines[k] for k in idxs}
    if set(rows) != set(order):
        return 0
    for pos, code in zip(idxs, order):
        lines[pos] = rows[code]
    s = s[:a] + "\n".join(lines) + s[b:]
    return 1

n1 = _reorder_table("**Table 1** Cohort composition", ["P1","P2","P3","P4","P5","P6"])
n2 = _reorder_table("**Table 2** Host-strain composition", ["P1","P2","P3","P4","P5","P6"])
if n1: log.append("  [ 1] Table 1 行序 -> P1..P6")
if n2: log.append("  [ 1] Table 2 行序 -> P1..P6")

io.open(DST, "w", encoding="utf-8", newline="\n").write(s)

print(f"写入 {DST}")
print(f"共 {len(log)} 类替换：")
for l in log:
    print(l)

# ---------- 复核：还剩多少未改的面板代号 ----------
print("\n=== 残留检查 ===")
# 注意：旧的 `.{50}...{50}` 正则要求前后各 50 字符，文本首尾/短行会漏列（曾漏报 1 处）。
# 改用滑动取窗口，确保每一处都被列出。
resid = [m for m in re.finditer(r"\b(?:US|FL|BR|CN|AF|AM)\b", s)]
print(f"裸代号残留 {len(resid)} 处（应均为真实地理语境）")
for m in resid:
    a = max(0, m.start() - 55)
    b = min(len(s), m.end() + 55)
    print("   ...", s[a:b].replace("\n", " "), "...")
