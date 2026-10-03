# -*- coding: utf-8 -*-
"""生成「口径」概念解释 SVG：同一对变量在三个样本集口径下的相关系数。"""
import io, math

def load(path):
    with io.open(path, encoding='utf-8') as f:
        head = f.readline().rstrip('\n').split('\t')
        return [dict(zip(head, ln.rstrip('\n').split('\t'))) for ln in f]

def pearson(xs, ys):
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    return sxy/(math.sqrt(sum((x-mx)**2 for x in xs))*math.sqrt(sum((y-my)**2 for y in ys)))

qc  = load(r'C:\SF_data\tools\report\qc_s2_bm2k15.tsv')       # 220
gea = load(r'C:\SF_data\tools\report\gea_input.tsv')          # 214
gea_runs = set(r['run'] for r in gea)

PAL = {"US":"#c0392b","BR":"#2471a3","AF":"#1e8449","AM":"#7d3c98","CN":"#d68910","FL":"#117a65"}

def pts(rows):
    return [(float(r['lat']), float(r['rate']), r['module'], r['run']) for r in rows]

A = pts(qc)                                   # 220 全部
B = [p for p in A if p[3] in gea_runs]        # 214 分析队列
C = [p for p in B if p[2] == 'US']            # 143 US 内部
excl = set(p[3] for p in A) - gea_runs        # 被剔除的 6 个

rA = pearson([p[0] for p in A], [p[1] for p in A])
rB = pearson([p[0] for p in B], [p[1] for p in B])
rC = pearson([p[0] for p in C], [p[1] for p in C])
print(f'rA={rA:+.4f} rB={rB:+.4f} rC={rC:+.4f}')

# ---- SVG 几何 ----
PX, PY, PW, PH = 0, 0, 192, 168          # 面板内容区
GAP = 10
X0 = 40
Y0 = 78
LAT0, LAT1 = -42, 48
RT0,  RT1  = 28, 104

def mx(lat):  return PX + (lat - LAT0)/(LAT1 - LAT0)*PW
def my(rt):   return PY + PH - (rt - RT0)/(RT1 - RT0)*PH

def panel_svg(ox, oy, data, title, rval, note, highlight_excl=False):
    s = [f'<g transform="translate({ox},{oy})">']
    s.append(f'<rect x="0" y="0" width="{PW}" height="{PH}" fill="#ffffff" stroke="#B4B2A9" stroke-width="0.5" rx="4"/>')
    # 网格线（rate=60/80/100）
    for gv in (60, 80, 100):
        gy = my(gv)
        s.append(f'<line x1="0" y1="{gy:.1f}" x2="{PW}" y2="{gy:.1f}" stroke="#EDEBE4" stroke-width="0.5"/>')
    for gl in (0,):
        gx = mx(gl)
        s.append(f'<line x1="{gx:.1f}" y1="0" x2="{gx:.1f}" y2="{PH}" stroke="#EDEBE4" stroke-width="0.5"/>')
    # 点（按模块合并成 path，圆头线帽等效圆点）
    by_mod = {}
    for lat, rt, mod, run in data:
        by_mod.setdefault(mod, []).append((lat, rt, run))
    for mod, arr in by_mod.items():
        d = ' '.join(f'M{mx(la):.1f} {my(rt):.1f}' for la, rt, _ in arr)
        s.append(f'<path d="{d}" fill="none" stroke="{PAL[mod]}" stroke-width="4.2" stroke-linecap="round" stroke-opacity="0.72"/>')
    if highlight_excl:
        for lat, rt, mod, run in data:
            if run in excl:
                s.append(f'<circle cx="{mx(lat):.1f}" cy="{my(rt):.1f}" r="4.4" fill="none" stroke="#993C1D" stroke-width="1.2"/>')
    # 轴刻度文字
    s.append(f'<text x="{mx(0):.1f}" y="{PH+14}" text-anchor="middle" font-size="11" fill="#5F5E5A">0°</text>')
    s.append(f'<text x="4" y="{PH+14}" font-size="11" fill="#5F5E5A">-40°</text>')
    s.append(f'<text x="{PW-2}" y="{PH+14}" text-anchor="end" font-size="11" fill="#5F5E5A">+45°</text>')
    s.append(f'<text x="-6" y="{my(100):.1f}" text-anchor="end" font-size="11" fill="#5F5E5A">100</text>')
    s.append(f'<text x="-6" y="{my(60):.1f}" text-anchor="end" font-size="11" fill="#5F5E5A">60</text>')
    # 面板标题 + r 值
    s.append(f'<text x="{PW/2}" y="-30" text-anchor="middle" font-size="13" font-weight="500" fill="#2C2C2A">{title}</text>')
    s.append(f'<text x="{PW/2}" y="-12" text-anchor="middle" font-size="12" fill="#5F5E5A">{note}</text>')
    s.append(f'<text x="{PW/2}" y="{PH+34}" text-anchor="middle" font-size="15" font-weight="500" fill="#A32D2D">r = {rval}</text>')
    s.append('</g>')
    return '\n'.join(s)

svg = []
svg.append('<svg viewBox="0 0 680 410" width="100%" role="img">')
svg.append('<title>同一个变量对在三个样本集口径下给出三个不同的相关系数</title>')
svg.append('<desc>纬度与比对率的散点图：全 220 下载样本 r=+0.489；分析队列 214 r=+0.433；US 模块内部 143 r=+0.023</desc>')
svg.append('<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>')

svg.append('<text x="340" y="30" text-anchor="middle" font-size="15" font-weight="500" fill="#2C2C2A">同一个问题：「比对率与纬度相关吗？」</text>')
svg.append('<text x="340" y="50" text-anchor="middle" font-size="13" fill="#5F5E5A">同一对变量、同一种算法（Pearson），只换样本集 —— 三个答案</text>')

svg.append(panel_svg(X0,               Y0, A, '(a) 全部下载样本', f'+{rA:.3f}', f'n = 220', True))
svg.append(panel_svg(X0+PW+GAP,       Y0, B, '(b) 分析队列', f'+{rB:.3f}', f'n = 214（剔除 6 个 BR 低率样本）'))
svg.append(panel_svg(X0+2*(PW+GAP),   Y0, C, '(c) US 模块内部', f'{rC:+.3f}', f'n = 143'))

# 底部结论
y = Y0 + PH + 56
svg.append(f'<rect x="36" y="{y}" width="608" height="86" rx="8" fill="#F1EFE8" stroke="#B4B2A9" stroke-width="0.5"/>')
svg.append(f'<text x="56" y="{y+26}" font-size="13" font-weight="500" fill="#2C2C2A">「口径」= 数字背后的精确定义：算给谁（样本集 n）、用什么变量、什么方法</text>')
svg.append(f'<text x="56" y="{y+50}" font-size="13" fill="#444441">论文里报 r 必须同时报 n 与样本定义 —— (a) 的 6 个圈出的 BR 低率样本（36–52%）正是把 r 从</text>')
svg.append(f'<text x="56" y="{y+72}" font-size="13" fill="#444441">+0.43 推到 +0.49 的杠杆点；而 (c) 说明共线只存在于模块之间，US 内部是干净的</text>')

svg.append('</svg>')

out = '\n'.join(svg)
io.open(r'C:\SF_data\tools\scope_widget.svg', 'w', encoding='utf-8').write(out)
print('svg bytes:', len(out.encode('utf-8')))
