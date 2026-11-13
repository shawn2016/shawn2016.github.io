# -*- coding: utf-8 -*-
"""
B 方案 · 参数化 DXF 生成器（单一数据源 = project.json）
输出：改造后 DXF / 叠加核对图 / 白底线稿
模型空间 1:1，单位 mm，Y 向上；LINE / ARC / CIRCLE / TEXT / 原生 DIMENSION 均为可独立选中实体。
"""
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'project.json'), encoding='utf-8') as f:
    P = json.load(f)

CAL = P['source']['calibration']
OX, OY = CAL['origin_px']
WMM, HMM = CAL['outer_mm']
SX = WMM / CAL['outer_px'][0]
SY = HMM / CAL['outer_px'][1]

# ---------------- 实体容器 ----------------
E = []


def line(a, b, layer='WALL'):
    E.append(('LINE', layer, a, b))


def arc(c, r, s, e, layer='DOOR'):
    E.append(('ARC', layer, c, r, s, e))


def circle(c, r, layer='FURN'):
    E.append(('CIRCLE', layer, c, r))


def text(p, s, h=260, layer='TEXT'):
    E.append(('TEXT', layer, p, h, s))


def rect(x0, y0, x1, y1, layer='FURN'):
    for a, b in [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                 ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]:
        line(a, b, layer)


def dashed_rect(x0, y0, x1, y1, dash, gap, layer):
    for ax, ay, bx, by in [(x0, y0, x1, y0), (x1, y0, x1, y1),
                           (x1, y1, x0, y1), (x0, y1, x0, y0)]:
        length = math.hypot(bx - ax, by - ay)
        n = max(1, int(length / (dash + gap)))
        for i in range(n):
            t0 = i * (dash + gap) / length
            t1 = min(1.0, (i * (dash + gap) + dash) / length)
            line((ax + (bx - ax) * t0, ay + (by - ay) * t0),
                 (ax + (bx - ax) * t1, ay + (by - ay) * t1), layer)


def cut(lo, hi, holes):
    seg, cur = [], lo
    for a, b in sorted(holes):
        if a > cur:
            seg.append((cur, min(a, hi)))
        cur = max(cur, b)
    if cur < hi:
        seg.append((cur, hi))
    return [(a, b) for a, b in seg if b - a > 1]


# ---------------- 墙体：240 厚双线，门洞处断开 ----------------
for w in P['walls']:
    holes = [tuple(h) for h in w.get('holes', [])]
    lo, hi, frm, to = w['lo'], w['hi'], w['from'], w['to']
    if w['axis'] == 'h':
        for y in (lo, hi):
            for a, b in cut(frm, to, holes):
                line((a, y), (b, y))
        for a, b in holes:
            line((a, lo), (a, hi))
            line((b, lo), (b, hi))
    else:
        for x in (lo, hi):
            for a, b in cut(frm, to, holes):
                line((x, a), (x, b))
        for a, b in holes:
            line((lo, a), (hi, a))
            line((lo, b), (hi, b))

# ---------------- 窗 ----------------
for w in P['windows']:
    lo, hi, frm, to = w['lo'], w['hi'], w['from'], w['to']
    if w['axis'] == 'h':
        ym = (lo + hi) / 2
        for y in (lo, ym, hi):
            line((frm, y), (to, y), 'WINDOW')
        line((frm, lo), (frm, hi), 'WINDOW')
        line((to, lo), (to, hi), 'WINDOW')
    else:
        xm = (lo + hi) / 2
        for x in (lo, xm, hi):
            line((x, frm), (x, to), 'WINDOW')
        line((lo, frm), (hi, frm), 'WINDOW')
        line((lo, to), (hi, to), 'WINDOW')


# ---------------- 门：LINE 门扇 + ARC 开启弧 ----------------
def door_v(x, a, b, inward=-1):
    width = b - a
    line((x, b), (x + inward * width, b), 'DOOR')
    s, e = (90, 180) if inward < 0 else (0, 90)
    arc((x, b), width, s, e, 'DOOR')


def door_h(y, a, b, inward=1, double=False):
    if not double:
        width = b - a
        line((a, y), (a, y + inward * width), 'DOOR')
        arc((a, y), width, 0, 90 if inward > 0 else -90, 'DOOR')
    else:
        m = (a + b) / 2
        width = m - a
        line((a, y), (a, y + inward * width), 'DOOR')
        arc((a, y), width, 0, 90, 'DOOR')
        line((b, y), (b, y + inward * width), 'DOOR')
        arc((b, y), width, 90, 180, 'DOOR')


for d in P['doors']:
    if d['axis'] == 'v':
        door_v(d['at'], d['a'], d['b'], d.get('inward', -1))
    else:
        door_h(d['at'], d['a'], d['b'], d.get('inward', 1), d.get('double', False))

# ---------------- 楼梯 ----------------
st = P['stair']
for i in range(st['count']):
    y = st['y0'] + i * st['step']
    line((st['x0'], y), (st['x1'], y), 'STAIR')

# ---------------- 通用图元（洁具 / 家具 / 拆改标记）----------------
for it in P['stair']['extras'] + P['primitives']:
    op = it['op']
    layer = it.get('layer', 'FURN')
    p = it['p']
    if op == 'rect':
        rect(p[0], p[1], p[2], p[3], layer)
    elif op == 'circle':
        circle((p[0], p[1]), it['r'], layer)
    elif op == 'line':
        line((p[0], p[1]), (p[2], p[3]), layer)
    elif op == 'arc':
        arc((p[0], p[1]), it['r'], it['s'], it['e'], layer)
    elif op == 'text':
        text((p[0], p[1]), it['s'], it.get('h', 260), layer)
    elif op == 'dashed_rect':
        dashed_rect(p[0], p[1], p[2], p[3], it.get('dash', 180), it.get('gap', 130), layer)

# ---------------- 房间名 / 图名（TEXT 实体）----------------
for lb in P['labels']:
    text((lb['p'][0], lb['p'][1]), lb['s'], lb.get('h', 300))

# ---------------- 原生 DIMENSION：测量值由几何端点计算 ----------------
DIMS = []
for d in P['dimensions']:
    p1 = tuple(d['p1'])
    p2 = tuple(d['p2'])
    meas = abs(p2[0] - p1[0]) if d['orient'] == 'h' else abs(p2[1] - p1[1])
    DIMS.append((d['orient'], p1, p2, d['off'], meas))

# ---------------- 写 ASCII DXF (R2000 / AC1015) ----------------
def gp(code, val):
    return '%d\n%s\n' % (code, val)


dxf = []
A = dxf.append
A(gp(0, 'SECTION') + gp(2, 'HEADER'))
A(gp(9, '$ACADVER') + gp(1, 'AC1015'))
A(gp(9, '$INSUNITS') + gp(70, 4))
A(gp(9, '$MEASUREMENT') + gp(70, 1))
A(gp(0, 'ENDSEC'))
A(gp(0, 'SECTION') + gp(2, 'TABLES'))
LAYERS = [('WALL', 7), ('WINDOW', 4), ('DOOR', 2), ('STAIR', 3),
          ('DIM', 8), ('TEXT', 7), ('FURN', 8), ('CHANGE', 1)]
A(gp(0, 'TABLE') + gp(2, 'LAYER') + gp(70, len(LAYERS)))
for name, color in LAYERS:
    A(gp(0, 'LAYER') + gp(2, name) + gp(70, 0) + gp(62, color) + gp(6, 'CONTINUOUS'))
A(gp(0, 'ENDTAB'))
A(gp(0, 'TABLE') + gp(2, 'STYLE') + gp(70, 1))
A(gp(0, 'STYLE') + gp(2, 'HZ') + gp(70, 0) + gp(40, 0) + gp(41, 1) +
  gp(50, 0) + gp(71, 0) + gp(42, 250) + gp(3, 'simsun.ttc') + gp(4, ''))
A(gp(0, 'ENDTAB') + gp(0, 'ENDSEC'))

# 每个关联标注一个匿名块，内含可见标注几何
A(gp(0, 'SECTION') + gp(2, 'BLOCKS'))
for i, (orient, p1, p2, off, meas) in enumerate(DIMS, start=1):
    A(gp(0, 'BLOCK') + gp(8, 'DIM') + gp(2, '*D%d' % i) + gp(70, 1) +
      gp(10, 0) + gp(20, 0) + gp(30, 0) + gp(3, '*D%d' % i) + gp(1, ''))
    txt = str(int(round(meas)))
    if orient == 'h':
        yd = p1[1] + off
        A(gp(0, 'LINE') + gp(8, 'DIM') + gp(10, p1[0]) + gp(20, yd) + gp(30, 0) +
          gp(11, p2[0]) + gp(21, yd) + gp(31, 0))
        for x, y in (p1, p2):
            A(gp(0, 'LINE') + gp(8, 'DIM') + gp(10, x) + gp(20, y) + gp(30, 0) +
              gp(11, x) + gp(21, yd + (80 if off > 0 else -80)) + gp(31, 0))
        A(gp(0, 'TEXT') + gp(8, 'DIM') + gp(7, 'HZ') + gp(10, (p1[0] + p2[0]) / 2) +
          gp(20, yd + 90) + gp(30, 0) + gp(40, 180) + gp(1, txt))
    else:
        xd = p1[0] + off
        A(gp(0, 'LINE') + gp(8, 'DIM') + gp(10, xd) + gp(20, p1[1]) +
          gp(30, 0) + gp(11, xd) + gp(21, p2[1]) + gp(31, 0))
        for x, y in (p1, p2):
            A(gp(0, 'LINE') + gp(8, 'DIM') + gp(10, x) + gp(20, y) + gp(30, 0) +
              gp(11, xd + (80 if off > 0 else -80)) + gp(21, y) + gp(31, 0))
        A(gp(0, 'TEXT') + gp(8, 'DIM') + gp(7, 'HZ') + gp(10, xd - 90) +
          gp(20, (p1[1] + p2[1]) / 2) + gp(30, 0) + gp(40, 180) + gp(1, txt) + gp(50, 90))
    A(gp(0, 'ENDBLK') + gp(8, 'DIM'))
A(gp(0, 'ENDSEC'))

A(gp(0, 'SECTION') + gp(2, 'ENTITIES'))
for e in E:
    t, layer = e[0], e[1]
    if t == 'LINE':
        (x1, y1), (x2, y2) = e[2], e[3]
        A(gp(0, 'LINE') + gp(8, layer) + gp(10, x1) + gp(20, y1) + gp(30, 0) +
          gp(11, x2) + gp(21, y2) + gp(31, 0))
    elif t == 'ARC':
        c, r, s, en = e[2], e[3], e[4], e[5]
        A(gp(0, 'ARC') + gp(8, layer) + gp(10, c[0]) + gp(20, c[1]) + gp(30, 0) +
          gp(40, r) + gp(50, s) + gp(51, en))
    elif t == 'CIRCLE':
        c, r = e[2], e[3]
        A(gp(0, 'CIRCLE') + gp(8, layer) + gp(10, c[0]) + gp(20, c[1]) +
          gp(30, 0) + gp(40, r))
    elif t == 'TEXT':
        p, h, s = e[2], e[3], e[4]
        A(gp(0, 'TEXT') + gp(8, layer) + gp(7, 'HZ') + gp(10, p[0]) + gp(20, p[1]) +
          gp(30, 0) + gp(40, h) + gp(1, s) + gp(50, 0))
for i, (orient, p1, p2, off, meas) in enumerate(DIMS, start=1):
    if orient == 'h':
        yd = p1[1] + off
        A(gp(0, 'DIMENSION') + gp(8, 'DIM') + gp(2, '*D%d' % i) + gp(10, p2[0]) +
          gp(20, yd) + gp(30, 0) + gp(11, (p1[0] + p2[0]) / 2) + gp(21, yd + 90) +
          gp(31, 0) + gp(70, 32) + gp(1, '<>') + gp(13, p1[0]) + gp(23, p1[1]) +
          gp(33, 0) + gp(14, p2[0]) + gp(24, p2[1]) + gp(34, 0) + gp(42, meas) +
          gp(3, 'STANDARD') + gp(50, 0))
    else:
        xd = p1[0] + off
        A(gp(0, 'DIMENSION') + gp(8, 'DIM') + gp(2, '*D%d' % i) + gp(10, xd) +
          gp(20, p2[1]) + gp(30, 0) + gp(11, xd - 90) + gp(21, (p1[1] + p2[1]) / 2) +
          gp(31, 0) + gp(70, 32) + gp(1, '<>') + gp(13, p1[0]) + gp(23, p1[1]) +
          gp(33, 0) + gp(14, p2[0]) + gp(24, p2[1]) + gp(34, 0) + gp(42, meas) +
          gp(3, 'STANDARD') + gp(50, 90))
A(gp(0, 'ENDSEC') + gp(0, 'EOF'))

DXF_PATH = os.path.join(HERE, '首层平面图_B方案_改造后.dxf')
with open(DXF_PATH, 'w', encoding='utf-8') as f:
    f.write(''.join(dxf))

# ---------------- 叠加核对图 / 白底线稿 ----------------
base = Image.open(P['source']['base_image']).convert('RGB')
W, H = base.size
COLORS = {'WALL': (214, 48, 48), 'WINDOW': (30, 150, 190), 'DOOR': (230, 140, 30),
          'STAIR': (40, 160, 90), 'FURN': (150, 90, 190), 'TEXT': (214, 48, 48),
          'DIM': (60, 90, 200), 'CHANGE': (235, 60, 60)}


def px(p):
    return (OX + p[0] / SX, OY - p[1] / SY)


def draw_entities(dr, font):
    for e in E:
        t, layer = e[0], e[1]
        col = COLORS.get(layer, (0, 0, 0))
        if t == 'LINE':
            dr.line([px(e[2]), px(e[3])], fill=col, width=2)
        elif t == 'ARC':
            c, r, s, en = e[2], e[3], e[4], e[5]
            box = [px((c[0] - r, c[1] + r)), px((c[0] + r, c[1] - r))]
            dr.arc(box, -en, -s, fill=col, width=2)
        elif t == 'CIRCLE':
            c, r = e[2], e[3]
            dr.ellipse([px((c[0] - r, c[1] + r)), px((c[0] + r, c[1] - r))],
                       outline=col, width=2)
        elif t == 'TEXT':
            p, h, s = e[2], e[3], e[4]
            x, y = px(p)
            dr.text((x, y - 10), s, fill=col, font=font)
    for orient, p1, p2, off, meas in DIMS:
        col = COLORS['DIM']
        if orient == 'h':
            yd = p1[1] + off
            dr.line([px((p1[0], yd)), px((p2[0], yd))], fill=col, width=1)
            for x, y in (p1, p2):
                dr.line([px((x, y)), px((x, yd))], fill=col, width=1)
            x, y = px(((p1[0] + p2[0]) / 2, yd + 90))
            dr.text((x, y - 14), str(int(meas)), fill=col, font=font)
        else:
            xd = p1[0] + off
            dr.line([px((xd, p1[1])), px((xd, p2[1]))], fill=col, width=1)
            for x, y in (p1, p2):
                dr.line([px((x, y)), px((xd, y))], fill=col, width=1)
            x, y = px((xd - 90, (p1[1] + p2[1]) / 2))
            dr.text((x, y - 14), str(int(meas)), fill=col, font=font)


font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Songti.ttc', 20)
clean = Image.new('RGB', (W, H), 'white')
draw_entities(ImageDraw.Draw(clean), font)
clean.save(os.path.join(HERE, 'B方案_线稿_白底.png'))

faded = Image.blend(base, Image.new('RGB', (W, H), 'white'), 0.72)
over = faded.convert('RGB')
draw_entities(ImageDraw.Draw(over), font)
over.save(os.path.join(HERE, 'B方案_叠加核对图.png'))

print('plan:', P['plan'], P['plan_title'])
print('DXF:', DXF_PATH)
print('entities:', len(E), 'dimensions:', len(DIMS))
print('by type:', {t: sum(1 for e in E if e[0] == t) for t in ('LINE', 'ARC', 'CIRCLE', 'TEXT')})
print('layers:', {l: sum(1 for e in E if e[1] == l) for l in ('WALL', 'WINDOW', 'DOOR', 'STAIR', 'FURN', 'TEXT', 'CHANGE')})
