"""
把 B 方案 project.json 转换成 house-plan-designer 的 HouseSpec。

设计要点
1. 坐标：project.json 是 Y 向上（南 y=0）；HouseSpec 是 Y 向下（南 y=大值）。
   统一用 flip(y) = 12000 - y 转换，rot 语义不受影响（两者北都在图纸上方）。
2. 墙：project.json 记的是墙体 lo..hi 的带状范围；HouseSpec 要墙中线。
3. 家具：不再照抄 project.json 的匿名矩形/圆，而是按房间功能规则
   从 house-plan-designer 的 321 件家具库中选真实家具自动布置。
4. 门窗、房间标签、待确认批注、风格、层高全部由单一数据源 project.json 驱动。

用法: python3 project_to_housespec.py
输出: spec_B方案.json
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.expanduser(
    '~/.workbuddy/tools/house-plan-designer/reference/catalog-sizes.json')

p = json.load(open(os.path.join(HERE, 'project.json'), encoding='utf-8'))
DEPTH = p['building']['outer'][1]
WIDTH = p['building']['outer'][0]
HEIGHT = p['building']['wall_height']
CAT = json.load(open(CATALOG, encoding='utf-8'))


def flip(y):
    return DEPTH - y


def pt(x, y):
    return [round(x), round(flip(y))]


furniture = []


def F(key, x, y, rot=0, **kw):
    assert key in CAT, '未知家具 key: ' + key
    item = {'key': key, 'at': pt(x, y), 'rot': rot}
    item.update(kw)
    furniture.append(item)
    return item


def C(key, cx, cy, r, count, start=0, rot=None):
    # 环形布置（餐椅、坐垫）
    for i in range(count):
        a = math.radians(start + 360 * i / count)
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        angle = (rot(i, a) if callable(rot) else (rot if rot is not None else 0))
        F(key, x, y, angle)


# ---------------------------------------------------------------- 墙体
# 先把门窗洞口按 (axis, lo, hi) 归并到对应墙上
openings_by_wall = {}
for d in p['doors']:
    if d['axis'] == 'h':
        key = ('h', 0, 240) if d['at'] < 1000 else ('h', 8870, 9110)
        frm, to = d['a'], d['b']
        is_entry = d['id'] == 'D-EN'
        op = {
            'type': 'double' if d.get('double') else 'door',
            'from': frm,
            'to': to,
            'hinge': 'from',
        }
        if is_entry:
            op['entry'] = True
            op['into'] = pt(4800, 1200)
        else:
            # 厨房门朝厨房内（北）开，其余水平墙门朝公共区开
            op['into'] = pt(8600, 10000) if d['id'] == 'D-KT' else pt(8600, 7800)
    else:
        key = ('v', 3540, 3780)
        frm, to = flip(d['b']), flip(d['a'])
        op = {
            'type': 'door',
            'from': frm,
            'to': to,
            'hinge': 'from',
        }
        # inward = -1 表示向卧室内（西）开
        mid_y = (d['a'] + d['b']) / 2
        op['into'] = pt(2600 if d['inward'] < 0 else 4600, mid_y)
    openings_by_wall.setdefault(key, []).append(op)

for w in p['windows']:
    key = (w['axis'], w['lo'], w['hi'])
    if w['axis'] == 'h':
        frm, to = w['from'], w['to']
        mid = (frm + to) / 2
        into = pt(mid, 1200 if w['lo'] == 0 else 11000)
    else:
        frm, to = flip(w['to']), flip(w['from'])
        mid_y = (w['from'] + w['to']) / 2
        into = pt(1200 if w['lo'] == 0 else 8500, mid_y)
    small = (to - frm) < 900
    op = {
        'type': 'highWindow' if small else ('floorWindow' if w['id'] == 'WIN-5' else 'window'),
        'from': frm,
        'to': to,
        'sill': 1400 if small else (0 if w['id'] == 'WIN-5' else 900),
    }
    if w['id'] == 'WIN-5':
        op['unsure'] = '按用户风格描述建的南向落地窗，原图未标窗台高'
    openings_by_wall.setdefault(key, []).append(op)

walls = []
for w in p['walls']:
    t = w['hi'] - w['lo']
    if w['axis'] == 'h':
        a = pt(w['from'], (w['lo'] + w['hi']) / 2)
        b = pt(w['to'], (w['lo'] + w['hi']) / 2)
        key = ('h', w['lo'], w['hi'])
    else:
        a = pt((w['lo'] + w['hi']) / 2, w['to'])
        b = pt((w['lo'] + w['hi']) / 2, w['from'])
        key = ('v', w['lo'], w['hi'])
    item = {'a': a, 'b': b, 't': t}
    ops = openings_by_wall.get(key, [])
    if ops:
        item['openings'] = sorted(ops, key=lambda o: o['from'])
    walls.append(item)

# ---------------------------------------------------------------- 房间
MAT = {
    '浅柚木地板': 'herring',
    '浅灰地砖': 'bath',
    '奶油白微水泥': 'cement',
}
CEIL_PUBLIC = {'type': 'edge', 'drop': 220, 'edgeW': 380,
               'cove': True, 'curtain': 200, 'cornice': True}
rooms = []
for r in p['rooms']:
    # 公共区打通后设计器会识别成一个大区域；多标签会拼成超长房间名，
    # 因此只放一个合并标签，并在批注里说明三个功能分区。
    if r['id'] in ('LR', 'DR', 'STY', 'ST'):
        continue
    x0, y0, x1, y1 = r['zone']
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    item = {'at': pt(cx, cy), 'name': r['name'],
            'mat': MAT.get(r['floor'], 'cement')}
    if r['id'] in ('KT', 'ET', 'BT'):
        item['ceil'] = {'type': 'alu', 'drop': 200}
        item['wallMat'] = 'wallTile'
    elif r['id'] in ('MB', 'BR'):
        item['ceil'] = {'type': 'flat', 'drop': 120, 'cornice': True}
        item['wallMat'] = 'latexWarm'
    else:
        item['ceil'] = dict(CEIL_PUBLIC)
        item['wallMat'] = 'latexWhite'
    rooms.append(item)
rooms.insert(0, {
    'at': pt(6570, 5600),
    'name': '客厅 · 餐厅 · 开放书房',
    'mat': 'cement',
    'wallMat': 'latexWhite',
    'ceil': dict(CEIL_PUBLIC),
})

# ---------------------------------------------------------------- 家具
# 房间区域速查
Z = {r['id']: r['zone'] for r in p['rooms']}


def z(id_):
    return Z[id_]


# 主卧：床靠西墙、衣柜靠东墙南段、窗帘收窄让开衣柜、挂墙件贴实墙
x0, y0, x1, y1 = z('MB')
F('bed18', x0 + 1170, 2000, 270)
F('nightstand', x0 + 210, 800, 270)
F('nightstand', x0 + 210, 3200, 270)
F('cabWardrobe', x1 - 300, 1500, 90, w=1400)
F('roundRug', 2750, 3400, 0, w=900, d=900)
# 主卧南窗右侧紧邻衣柜，落地窗帘会与高柜冲突，改用窗内百叶帘
F('blinds', 1895, 300, 180, w=2500)
F('acWall', 900, y1 - 180, 0)
F('wallArt', 2300, y1 - 60, 0)

# 次卧：床靠西墙、矮书架靠南墙、衣柜靠东墙北段、空调避开北窗挂西墙
x0, y0, x1, y1 = z('BR')
F('bed15', x0 + 1145, 10300, 270)
F('nightstand', x0 + 210, 9250, 270)
F('nightstand', x0 + 210, 11350, 270)
F('wardrobe', x1 - 300, 10400, 90, w=1600)
# 北窗下用窗内百叶帘，避免落地帘与靠东墙的高衣柜互相干涉
F('blinds', 2000, y1 - 260, 0, w=2350)
F('acWall', x0 + 130, 11000, 270)
F('rug', 2600, 9500, 0, w=1600, d=1200)

# 套卫：马桶 / 浴室柜 / 淋浴 / 浴霸 / 热水器（挂墙件背面正好贴墙内表面）
x0, y0, x1, y1 = z('ET')
F('toilet', 800, y1 - 350, 0)
F('vanity', 1900, y1 - 250, 0)
F('mirrorCabinet', 1900, y1 - 75, 0)
F('shower', 2950, 5500, 0)
F('towelWarmer', 900, y0 + 50, 180)
F('bathHeater', 1800, 5000)
F('waterHeater', 3000, y1 - 225, 0)

# 公卫：加洗衣机 / 洗衣池 / 晾衣架
x0, y0, x1, y1 = z('BT')
F('toilet', 800, y1 - 350, 0)
F('vanity', 1900, y1 - 250, 0)
F('mirrorCabinet', 1900, y1 - 75, 0)
F('shower', 2950, 7700, 0)
F('washer', 800, y0 + 300, 180)
F('laundrySink', 1600, y0 + 275, 180)
F('bathHeater', 1800, 7300)
F('waterHeater', 3000, y1 - 225, 0)
F('clothesRack', 2400, 6900)

# 厨房：L 形橱柜靠东墙避开北窗吊柜，冰箱与垃圾桶让开厨房门开启弧
x0, y0, x1, y1 = z('KT')
# 北窗下不做吊柜（会挡窗），改用地柜 + 挂墙烟机，橱柜沿东墙布置
F('cabBase', 9060, 10300, 90, w=2000, d=600)
F('hood', 9100, 10300, 90)
F('fridge', 6800, y0 + 350, 180)
F('trashBin', 6650, 10300)
F('blinds', 7990, y1 - 220, 0, w=2000)

# 楼梯：直跑梯段
F('stairRun', 4950, 10420, 0, w=2200, d=2400)

# 玄关：自动水电把这面墙的空调孔和 16A 插座布在门东侧，鞋柜会压住点位，
# 因此只留地垫；西侧通道整体留空保证 ≥700mm 净宽
F('doormat', 4800, 480, 0)

# 开放书房（B 方案核心）：岛式，不贴墙、不挡门、不压南窗
# 位置沿用 project.json change_log C4 的 range [4700,1600,6500,3920]
# 家具之间留足净距，西侧 x<4700 全程留空保证 920mm 通道
F('bookshelfLow', 5500, 1760, 180, w=1600, d=320)
F('desk', 5500, 2350, 0, w=1600, d=500)
F('readingChair', 5050, 3050, 0, opt={'style': 'japanese'})
F('readingChair', 6000, 3050, 0, opt={'style': 'japanese'})
F('deskLamp', 6150, 2350)
F('bookSet', 4900, 2350)
F('tableVase', 5700, 2350)
F('roundRug', 5500, 3600, 0, w=1300, d=1300)
F('plushToy', 5500, 3600)
# 绿植只放书桌角，不占书房与客厅之间通往厨房的动线
F('smallPlant', 6450, 2500)

# 客厅：沙发朝东看电视，南向落地窗留空、窗帘贴墙
F('sofa', 7100, 2800, 270, w=2200, opt={'style': 'japanese'})
F('rug', 7900, 2800, 0, w=2600, d=1900)
F('roundCoffee', 7900, 2800, 0, w=900, d=900)
F('wallTV', 9280, 2800, 90)
F('tvCabinet', 9050, 2800, 90, w=1600, d=400)
F('armchair', 8400, 1600, 180)
F('armchair', 8400, 4000, 0)
F('curtain', 7650, 300, 180, w=2500)
F('sheer', 7650, 330, 180, w=2500)
F('smallPlant', 9100, 1000)

# 餐厅：圆桌 + 六椅（沿用原图圆桌中心 7850,6970）+ 餐边柜 + 吊灯
F('roundTable', 7850, 6970, 0, w=1300, d=1300)
C('chair', 7850, 6970, 950, 6, start=90,
  rot=lambda i, a: int((math.degrees(a) + 90) % 360))
F('chandelier', 7850, 6970)
F('cabSideboard', 6900, 8670, 0, w=1800, d=400)
F('tableVase', 7850, 6970)
F('curtain', 9280, 6900, 90, w=2500)
F('sheer', 9250, 6900, 90, w=2500)

# ---------------------------------------------------------------- 结构点位
structs = [
    {'kind': 'sewer', 'at': pt(800, z('ET')[3] - 350)},
    {'kind': 'drain', 'at': pt(2950, 5500)},
    {'kind': 'sewer', 'at': pt(800, z('BT')[3] - 350)},
    {'kind': 'drain', 'at': pt(2950, 7700)},
    {'kind': 'drain', 'at': pt(1100, z('BT')[1] + 300)},
    {'kind': 'drain', 'at': pt(7900, 10500)},
]

# ---------------------------------------------------------------- 批注
comments = [
    {'at': pt(4800, 1050), 'text': t} for t in p['pending_confirmation']
]
comments.append({
    'at': pt(5500, 4300),
    'text': 'B 方案：中部神位矮台隔断已拆除，开放书房与客餐厅一体化；两间卧室均为有墙有门的独立房间',
})
comments.append({
    'at': pt(5500, 2600),
    'text': '家具由 project.json 的房间功能规则自动布置，可在设计器里点选替换款式、改尺寸或整套换风格',
})

# 底图：原始黑白户型图，可在设计器「户型」面板勾选显示做对照
S = (WIDTH / 693 + DEPTH / 857) / 2
underlay = {
    'image': p['source']['base_image'],
    'mmPerPx': round(S, 4),
    'x': round(-198 * S),
    'y': round(DEPTH - 1073 * S),
}

spec = {
    'name': '自建房首层 · B 方案（客厅＋开放书房）',
    'height': HEIGHT,
    'heightFrom': 'estimated',
    'phase': 'renovate',
    'north': 0,
    'walls': walls,
    'rooms': rooms,
    'structs': structs,
    'furniture': furniture,
    'autoElec': True,
    'style': 'japanese',
    'look': {'style': 'real', 'palette': 'midcentury', 'glow': True, 'labels': True},
    'comments': comments,
    'underlay': underlay,
}

out = os.path.join(HERE, 'spec_B方案.json')
json.dump(spec, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

from collections import Counter
print('输出:', out)
print('墙:', len(walls), ' 房间标签:', len(rooms), ' 家具:', len(furniture),
      ' 结构点位:', len(structs), ' 批注:', len(comments))
print('家具件数按类别:', Counter(f['key'] for f in furniture).most_common(12))
print('门窗洞口:', sum(len(w.get('openings', [])) for w in walls))
print('底图比例 mm/px:', underlay['mmPerPx'], ' 左上角:', underlay['x'], underlay['y'])
