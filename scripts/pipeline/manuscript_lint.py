# -*- coding: utf-8 -*-
"""稿件机械体检：数字一致性 / 术语 / 引用完整性 / 格式。
只报事实，不下判断。"""
import io, re, sys
from collections import Counter, defaultdict

P = r"C:/同步/BaiduSyncdisk/北方民族大学/科研项目/公共数据/气候昆虫基因/昆虫气候基因组/03_论文/manuscript_en_v2_2026-09-25.md"
s = io.open(P, encoding="utf-8").read()
low = s.lower()
issues = defaultdict(list)


def bad(tag, msg):
    issues[tag].append(msg)


print("=" * 70)
print("稿件机械体检 —", P.split("/")[-1])
print("=" * 70)
print("字数 %d，行数 %d" % (len(s), s.count("\n")))

# ---------- 1. 旧面板代号残留 ----------
OLD = ["US", "FL", "BR", "CN", "AF", "AM"]
for m in re.finditer(r"\b(?:US|FL|BR|CN|AF|AM)\b", s):
    a = max(0, m.start() - 70); b = min(len(s), m.end() + 70)
    ctx = s[a:b].replace("\n", " ")
    if "continental US" in ctx or "~~AF/AM panel naming" in ctx:
        continue
    bad("旧代号", "…%s…" % ctx)

# ---------- 2. LFMM 措辞 ----------
for m in re.finditer(r"LFMM(?!-type)(?!2)\w*", s):
    a = max(0, m.start() - 60); b = min(len(s), m.end() + 60)
    bad("LFMM措辞", "…%s…" % s[a:b].replace("\n", " "))

# ---------- 3. 图表引用完整性 ----------
refs_used = set(re.findall(r"(?:Fig\.|Figure)\s*(S?\d+[a-c]?)", s))
tabs_used = set(re.findall(r"Table\s*(S?\d+)", s))
figs_defined = set(re.findall(r"\*\*(?:Fig\.|Figure)\s*(S?\d+)\*\*", s))
tabs_defined = set(re.findall(r"\*\*(?:Table)\s*(S?\d+)\*\*", s))
for f in sorted(figs_defined - refs_used):
    bad("图引用", "定义了 Fig.%s 但正文从未引用" % f)
for t in sorted(tabs_defined - tabs_used - {"S1"}):
    if t not in ("S1",):
        bad("表引用", "定义了 Table %s 但正文从未引用" % t)
print("\n图：定义 %d 个，正文引用 %d 个" % (len(figs_defined), len(refs_used)))
print("表：定义 %d 个，正文引用 %d 个" % (len(tabs_defined), len(tabs_used)))
print("  图定义:", sorted(figs_defined))
print("  表定义:", sorted(tabs_defined))

# ---------- 4. 章节编号连续性 ----------
secs = re.findall(r"^#{2,3}\s+(\d+(?:\.\d+)?)\.?\s", s, re.M)
print("\n章节:", secs)
for i in range(len(secs) - 1):
    pass  # 4.6->4.7 这类跳号在正文里常见，只打印不报错

# ---------- 5. 占位符 ----------
cites = re.findall(r"\[CITE:([^\]]{0,70})", s)
print("\n[CITE: 占位] %d 处" % len(cites))
for c in cites:
    print("   -", c.strip()[:70])

# ---------- 6. 关键数字是否出现 ----------
KEY = {
    "214": "分析队列", "220": "下载总数", "143": "P1", "12 countries": "国家数",
    "16,230,602": "位点数", "2.30%": "partial R2", "0.9485": "lambda",
    "13,659": "LOC背景", "2.42": "长度偏差倍数", "4.3 × 10⁻¹⁵⁴": "长度偏差p",
    "+0.534": "两法r", "+0.508": "两法rho", "196 sites": "top1000重叠",
    "550": "≥3面板共享", "556": "敏感性后共享", "7,643": "m_eff",
    "1,010,000": "LFMM位点", "47 sites": "LFMM显著", "2,565": "候选基因",
    "0.0005": "氧化应激p", "0.0010": "HSP p", "0.055": "敏感性后滞育p",
    "+0.489": "全队列r(rate,lat)", "+0.023": "US内部r", "−0.262": "r(PC1,rate)",
    "22.9": "US纬度跨度", "12.16": "P5深度", "84.25": "P2比对率",
}
print("\n关键数字出现情况:")
for k, v in KEY.items():
    if k not in s:
        bad("关键数字", "**缺失**: %s (%s)" % (k, v))

# ---------- 7. 数字格式一致性 ----------
# 7.1 百分比写法
pct = re.findall(r"\d+\.\d+%", s)
bad_pct = [x for x in pct if 0 < float(x[:-1]) < 1 and not x.startswith("0.")]
# 7.2 p 值格式
ps = re.findall(r"\*p\*\s*=\s*([0-9.e−–-]+)", s)
fmt = Counter()
small = []
for x in ps:
    if "×" in x or "10" in x:
        fmt["科学计数"] += 1
        continue
    try:
        v = float(x)
    except ValueError:
        continue
    if v < 0.001:
        fmt["<0.001"] += 1
        small.append(x)
    else:
        fmt["小数"] += 1
print("\np 值写法分布:", dict(fmt))
for x in small:
    bad("p值格式", "*p* = %s 小于 0.001，建议用科学计数法" % x)

# 7.3 千分位
nums = re.findall(r"(?<![\d.])\d{5,}(?![\d])", s)
for x in set(nums):
    if len(x) >= 5:
        bad("大数字", "%s 未加千分位" % x)

# ---------- 8. 术语/拼写 ----------
TYPO = {
    "recieve": "receive", "seperate": "separate", "occurance": "occurrence",
    "neccessary": "necessary", "comparable": "comparable", "reciept": "receipt",
    "Fig.1": "Fig. 1", "Table1": "Table 1", "et.al": "et al.",
    "  ": "双空格", " ,": "逗号前空格", " .": "句号前空格",
}
for k, v in TYPO.items():
    n = s.count(k)
    if n and k not in ("  ", " ,", " ."):
        bad("拼写/格式", "%r ×%d  → %s" % (k, n, v))
for k in ["  ", " ,", " ."]:
    n = s.count(k)
    if n:
        bad("排版", "%r ×%d" % (k, n))

# ---------- 9. 拉丁学名斜体 ----------
for sp in ["Spodoptera frugiperda", "S. frugiperda", "Chlordea", "Agrotis"]:
    for m in re.finditer(re.escape(sp), s):
        a = m.start()
        pre = s[max(0, a - 12):a]
        if "*" not in pre[-10:]:
            ctx = s[max(0, a - 40):m.end() + 40].replace("\n", " ")
            bad("学名斜体", "…%s…" % ctx)

# ---------- 10. 悬空/占位符类 ----------
for pat, tag in [(r"TODO|FIXME|XXX|\?\?\?", "待办残留"),
                 (r"^\s*-$", "空列表项"),
                 (r"\bvery\s+(very|important|significant)\b", "弱表述"),
                 (r"\b(prove|prove[sd]?|demonstrate that)\b", "强断言")]:
    for m in re.finditer(pat, s, re.M | re.I):
        a = max(0, m.start() - 50); b = min(len(s), m.end() + 50)
        bad(tag, "…%s…" % s[a:b].replace("\n", " "))

# ---------- 汇总 ----------
print("\n" + "=" * 70)
if not issues:
    print("机械检查：未发现问题")
else:
    for tag in sorted(issues):
        print("\n【%s】%d 项" % (tag, len(issues[tag])))
        for x in issues[tag][:12]:
            print("   •", x)
        if len(issues[tag]) > 12:
            print("   … 另有 %d 项" % (len(issues[tag]) - 12))
