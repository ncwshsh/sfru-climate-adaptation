# -*- coding: utf-8 -*-
"""
manuscript_en_v1_2026-09-24.md -> academic-paper HTML (for tencent-docx html-to-docx)

设计要点：
- 内容零改写：所有正文、表格、图注、[CITE: ...] 占位符原样搬运
- 仅做 Markdown -> 语义 HTML 的结构映射，不增删语义
- 遵循 doc-typeset base.md 硬约束：
    * :root 变量块完整，无裸值
    * 结构化内容一律 <table>，含 thead/tbody
    * 顶层 <section> 只用于 cover / body 两个真实页面边界
    * 关键 CSS 属性每块显式声明
    * 无装饰性短横线
"""
import re
import sys
import html as _h
import io
from pathlib import Path

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\同步\BaiduSyncdisk\北方民族大学\科研项目\公共数据\气候昆虫基因\昆虫气候基因组\03_论文\manuscript_en_v1_2026-09-24.md")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(r"C:\SF_data\tools\_manuscript_en.html")

text = SRC.read_text(encoding="utf-8")
lines = text.split("\n")

# ---------------- 行内转换 ----------------
def esc(s: str) -> str:
    return _h.escape(s, quote=False)

def inline(s: str) -> str:
    """Markdown 行内 -> HTML 行内。顺序重要：先转义，再做标记替换。"""
    s = esc(s)
    # 行内代码 `x`
    s = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", s)
    # 粗体 **x**
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    # 斜体 *x*（避开已生成的标签属性；此处内容里 * 只用于斜体）
    s = re.sub(r"(?<![\w<])?\*([^*\n]+?)\*(?![\w>])", r"<em>\1</em>", s)
    # 上标标记（稿件用 Unicode 上标，保持原样即可，无需转换）
    return s

def is_table_sep(l: str) -> bool:
    return bool(re.match(r"^\s*\|?[\s:\-|]+\|[\s:\-|]*$", l)) and "-" in l

# 表格单元格内的字面竖线保护（如 |*z*| 统计量记号）
# Markdown 规范用 \| 转义，但本稿写作 |*z*|，需在切分前保护
_LITERAL_PIPE = "\x00PIPE\x00"

def protect_pipes(l: str) -> str:
    """把表格单元格内的竖线保护起来，避免被当作列分隔符。
    稿件使用 Markdown 转义写法 \\|*z*\\|（统计量绝对值记号），
    故先归一化 \\| -> | 再做保护。"""
    l = l.replace("\\|", "|")
    return re.sub(r"\|(\*?[A-Za-z][A-Za-z0-9_]*\*?)\|", _LITERAL_PIPE + r"\1" + _LITERAL_PIPE, l)

def restore_pipes(s: str) -> str:
    return s.replace(_LITERAL_PIPE, "|")

def split_row(l: str):
    l = l.strip()
    if l.startswith("|"):
        l = l[1:]
    if l.endswith("|"):
        l = l[:-1]
    return [restore_pipes(c.strip()) for c in l.split("|")]

def align_of(sep: str):
    out = []
    for c in split_row(sep):
        c = c.strip()
        if c.startswith(":") and c.endswith(":"):
            out.append("center")
        elif c.endswith(":"):
            out.append("right")
        else:
            out.append("left")
    return out

# ---------------- 主解析 ----------------
blocks = []          # 每个元素是 (kind, payload)
i = 0
n = len(lines)

while i < n:
    line = lines[i]

    # 空行
    if not line.strip():
        i += 1
        continue

    # 水平线 -> 不输出装饰线（base.md §g：仅章节分隔可用 divider，此处按语义跳过）
    if re.match(r"^\s*---+\s*$", line):
        i += 1
        continue

    # 标题
    m = re.match(r"^(#{1,6})\s+(.*)$", line)
    if m:
        lvl = len(m.group(1))
        blocks.append(("h", (lvl, m.group(2).strip())))
        i += 1
        continue

    # 引用块 > （稿件里 Terminology / Reference scaffolding 提示）
    if line.lstrip().startswith(">"):
        buf = []
        while i < n and lines[i].lstrip().startswith(">"):
            buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
            i += 1
        blocks.append(("quote", buf))
        continue

    # 代码块 ```（angsd 命令行）
    if line.strip().startswith("```"):
        i += 1
        buf = []
        while i < n and not lines[i].strip().startswith("```"):
            buf.append(lines[i])
            i += 1
        i += 1
        blocks.append(("code", buf))
        continue

    # 表格
    if line.strip().startswith("|") and i + 1 < n and is_table_sep(lines[i + 1]):
        header = split_row(protect_pipes(line))
        aligns = align_of(lines[i + 1])
        i += 2
        rows = []
        while i < n and lines[i].strip().startswith("|"):
            rows.append(split_row(protect_pipes(lines[i])))
            i += 1
        blocks.append(("table", (header, aligns, rows)))
        continue

    # 有序列表
    m = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
    if m:
        buf = []
        while i < n:
            mm = re.match(r"^\s*(\d+)\.\s+(.*)$", lines[i])
            if not mm:
                # 续行（缩进的行归属于上一条）
                if lines[i].startswith("   ") and lines[i].strip() and buf:
                    buf[-1] = buf[-1] + " " + lines[i].strip()
                    i += 1
                    continue
                break
            buf.append(mm.group(2).strip())
            i += 1
        blocks.append(("ol", buf))
        continue

    # 无序列表
    m = re.match(r"^\s*[-*]\s+(.*)$", line)
    if m:
        buf = []
        while i < n:
            mm = re.match(r"^\s*[-*]\s+(.*)$", lines[i])
            if not mm:
                if lines[i].startswith("   ") and lines[i].strip() and buf:
                    buf[-1] = buf[-1] + " " + lines[i].strip()
                    i += 1
                    continue
                break
            buf.append(mm.group(1).strip())
            i += 1
        blocks.append(("ul", buf))
        continue

    # 普通段落（合并连续行）
    buf = [line.strip()]
    i += 1
    while i < n and lines[i].strip() and not re.match(r"^(#{1,6}\s|\s*[-*]\s|\s*\d+\.\s|\||>|```|\s*---+\s*$)", lines[i]):
        buf.append(lines[i].strip())
        i += 1
    blocks.append(("p", " ".join(buf)))

print(f"[parse] blocks={len(blocks)}", file=sys.stderr)

# ---------------- 分节：识别封面元信息 / 正文 ----------------
# 标题 = 第 1 个 h1
title = ""
rest = []
for k, v in blocks:
    if k == "h" and v[0] == 1 and not title:
        title = v[1]
        continue
    rest.append((k, v))
blocks = rest

# 正文头部元信息（Running head / Version / Target journal / Citation style）
meta = []
while blocks and blocks[0][0] == "p":
    p = blocks[0][1]
    if re.match(r"^\*\*(Running head|Version|Target journal|Citation style)", p):
        meta.append(p)
        blocks.pop(0)
    else:
        break

# ---------------- 生成 HTML ----------------
def render_block(kind, payload, out, ctx):
    if kind == "h":
        lvl, txt = payload
        # h1 是文档主标题，不应出现在正文（已提取）；正文从 h2 起
        if lvl == 1:
            out.append(f'<h2 id="section-{ctx["sec"]}">{inline(txt)}</h2>')
            ctx["sec"] += 1
            return
        if lvl == 2:
            out.append(f'<h2 id="section-{ctx["sec"]}">{inline(txt)}</h2>')
            ctx["sec"] += 1
            return
        if lvl == 3:
            out.append(f'<h3>{inline(txt)}</h3>')
            return
        out.append(f'<h4>{inline(txt)}</h4>')
        return

    if kind == "p":
        out.append(f"<p>{inline(payload)}</p>")
        return

    if kind == "quote":
        inner = "".join(f"<p>{inline(x)}</p>" for x in payload if x.strip())
        out.append(
            '<table class="note-card"><tr><td>'
            + inner +
            "</td></tr></table>"
        )
        return

    if kind == "code":
        body = "\n".join(esc(x) for x in payload)
        out.append(f'<pre class="codeblock"><code>{body}</code></pre>')
        return

    if kind == "table":
        header, aligns, rows = payload
        th = "".join(
            f'<th style="text-align: {aligns[j] if j < len(aligns) else "left"};">{inline(c)}</th>'
            for j, c in enumerate(header)
        )
        trs = []
        for r in rows:
            tds = "".join(
                f'<td style="text-align: {aligns[j] if j < len(aligns) else "left"};">{inline(c)}</td>'
                for j, c in enumerate(r)
            )
            trs.append(f"<tr>{tds}</tr>")
        out.append(
            '<table class="three-line-table"><thead><tr>'
            + th
            + "</tr></thead><tbody>"
            + "".join(trs)
            + "</tbody></table>"
        )
        return

    if kind == "ol":
        items = "".join(f"<li>{inline(x)}</li>" for x in payload)
        out.append(f'<ol class="body-list">{items}</ol>')
        return

    if kind == "ul":
        items = "".join(f"<li>{inline(x)}</li>" for x in payload)
        out.append(f'<ul class="body-list">{items}</ul>')
        return


CSS_TOKENS = """:root {
    --fs-title: var(--typography-fontSize-title, 18pt);
    --fs-h1: var(--typography-fontSize-h1, 15pt);
    --fs-h2: var(--typography-fontSize-h2, 14pt);
    --fs-h3: var(--typography-fontSize-h3, 12pt);
    --fs-body: var(--typography-fontSize-body, 12pt);
    --fs-abstract: var(--typography-fontSize-abstract, 11pt);
    --fs-caption: var(--typography-fontSize-caption, 10.5pt);
    --fs-footnote: var(--typography-fontSize-footnote, 9pt);
    --ff-heading: var(--typography-fontFamily-heading, "Times New Roman", serif);
    --ff-body: var(--typography-fontFamily-body, "Times New Roman", serif);
    --ff-mono: var(--typography-fontFamily-code, "Courier New", monospace);
    --lh-body: var(--typography-lineHeight-body, 1.5);
    --lh-abstract: var(--typography-lineHeight-abstract, 1.25);
    --fw-bold: var(--typography-fontWeight-heading, 700);
    --fw-normal: var(--typography-fontWeight-body, 400);
    --color-primary: var(--color-primary, #000000);
    --color-text: var(--color-text, #000000);
    --color-muted: #555555;
    --color-border: var(--color-tableBorder, #000000);
    --color-bg: var(--color-background, #ffffff);
    --color-panel: #f4f4f4;
    --spacing-paragraph: var(--spacing-paragraph, 0.5em);
    --spacing-section: var(--spacing-sectionGap, 1.5em);
    --spacing-block: 1em;
    --margin-page: var(--layout-marginTop, 2.5cm);
    --page-content-width: 16.0cm;
}"""


def main():
    head = []
    body_cover = []
    body_main = []

    ctx = {"sec": 1}

    # 正文渲染
    out = []
    for k, v in blocks:
        render_block(k, v, out, ctx)
    body_main = out

    # 封面
    cover_lines = [
        '<section role="cover">',
        f'<p class="cover-eyebrow" style="text-align: center;">MANUSCRIPT DRAFT v2 &middot; 2026-09-25</p>',
        f'<h1 class="cover-title" style="text-align: center;">{inline(title)}</h1>',
    ]
    if meta:
        rows = []
        for m in meta:
            mm = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", m)
            if mm:
                rows.append(
                    f'<tr><td class="cover-k" style="text-align: right;">{inline(mm.group(1))}</td>'
                    f'<td class="cover-v" style="text-align: left;">{inline(mm.group(2))}</td></tr>'
                )
        if rows:
            cover_lines.append(
                '<table class="cover-info-list"><tbody>' + "".join(rows) + "</tbody></table>"
            )
    cover_lines.append("</section>")

    html = []
    html.append('<!DOCTYPE html>')
    html.append('<html lang="en">')
    html.append("<head>")
    html.append('<meta charset="UTF-8">')
    html.append('<meta name="docx-page-size" content="A4">')
    html.append(f"<title>{esc(title)}</title>")
    html.append("<style>")
    html.append(CSS_TOKENS)
    html.append(f"""
    * {{ box-sizing: border-box; }}
    body {{
      font-family: var(--ff-body);
      font-size: var(--fs-body);
      line-height: var(--lh-body);
      color: var(--color-text);
      background: var(--color-bg);
    }}
    p {{
      margin-top: 0;
      margin-bottom: var(--spacing-paragraph);
      text-align: justify;
    }}
    h1, h2, h3, h4 {{
      font-family: var(--ff-heading);
      font-weight: var(--fw-bold);
      color: var(--color-primary);
      text-align: left;
    }}
    h2 {{
      font-size: var(--fs-h1);
      margin-top: var(--spacing-section);
      margin-bottom: var(--spacing-paragraph);
    }}
    h3 {{
      font-size: var(--fs-h2);
      margin-top: var(--spacing-block);
      margin-bottom: var(--spacing-paragraph);
    }}
    h4 {{
      font-size: var(--fs-h3);
      margin-top: var(--spacing-block);
      margin-bottom: var(--spacing-paragraph);
    }}
    .cover-eyebrow {{
      text-align: center;
      font-size: var(--fs-caption);
      letter-spacing: 0.12em;
      color: var(--color-muted);
      margin-top: 6em;
      margin-bottom: 1.2em;
    }}
    .cover-title {{
      text-align: center;
      font-size: var(--fs-title);
      margin-bottom: var(--spacing-section);
    }}
    .cover-info-list {{
      border-collapse: collapse;
      margin: 2.5em auto 0 auto;
      width: auto;
    }}
    .cover-info-list td {{
      padding: 0.3em 0.6em;
      font-size: var(--fs-abstract);
      vertical-align: top;
      border: none;
    }}
    .cover-k {{
      font-weight: var(--fw-bold);
      white-space: nowrap;
      color: var(--color-primary);
    }}
    .abstract {{
      margin-top: var(--spacing-section);
      margin-bottom: var(--spacing-section);
    }}
    .abstract-heading {{
      font-family: var(--ff-heading);
      font-weight: var(--fw-bold);
      font-size: var(--fs-h2);
      text-align: left;
      margin-bottom: var(--spacing-paragraph);
    }}
    .keywords {{
      font-size: var(--fs-abstract);
      text-align: left;
      margin-top: var(--spacing-paragraph);
    }}
    .note-card {{
      border-collapse: collapse;
      width: 100%;
      margin-top: var(--spacing-paragraph);
      margin-bottom: var(--spacing-block);
    }}
    .note-card td {{
      background: var(--color-panel);
      border-left: 3px solid var(--color-muted);
      padding: 0.6em 0.9em;
      font-size: var(--fs-abstract);
    }}
    .note-card p {{
      margin-bottom: 0.4em;
      text-align: left;
    }}
    pre.codeblock {{
      font-family: var(--ff-mono);
      font-size: var(--fs-footnote);
      background: var(--color-panel);
      padding: 0.6em 0.9em;
      margin-top: var(--spacing-paragraph);
      margin-bottom: var(--spacing-block);
    }}
    pre.codeblock code {{
      font-family: var(--ff-mono);
      font-size: var(--fs-footnote);
    }}
    code {{
      font-family: var(--ff-mono);
      font-size: var(--fs-abstract);
    }}
    .three-line-table {{
      border-collapse: collapse;
      width: 100%;
      margin-top: var(--spacing-paragraph);
      margin-bottom: var(--spacing-block);
    }}
    .three-line-table thead tr:first-child {{ border-top: 1.5pt solid var(--color-border); }}
    .three-line-table thead tr:last-child {{ border-bottom: 0.75pt solid var(--color-border); }}
    .three-line-table tbody tr:last-child {{ border-bottom: 1.5pt solid var(--color-border); }}
    .three-line-table th {{
      font-family: var(--ff-heading);
      font-weight: var(--fw-bold);
      font-size: var(--fs-caption);
      padding: 0.35em 0.55em;
      border-left: none;
      border-right: none;
    }}
    .three-line-table td {{
      font-size: var(--fs-caption);
      padding: 0.35em 0.55em;
      border-left: none;
      border-right: none;
    }}
    .body-list {{
      padding-left: 1.6em;
      margin-bottom: var(--spacing-block);
    }}
    .body-list li {{
      font-size: var(--fs-body);
      margin-bottom: 0.35em;
      text-align: justify;
    }}
    """)
    html.append("</style>")
    html.append("</head>")
    html.append("<body>")
    html.extend(cover_lines)

    # 正文 section
    html.append('<section role="body" data-page-restart="1">')
    html.extend(body_main)
    html.append("</section>")
    html.append("</body>")
    html.append("</html>")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(html), encoding="utf-8")
    print(f"[ok] wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(f"[stats] h2={ctx['sec']-1}")


main()
