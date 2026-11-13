#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按 cad/project.json 的 B 方案参数化生成 SketchUp 3D 概念模型。

单一数据源：project.json（轴网 / walls / windows / doors / rooms / stair / primitives）
执行通道：本地 SketchUp MCP 桥的 /ruby/execute（127.0.0.1:28080）
单位纪律：project.json 全为 mm；SketchUp Ruby API 内部恒为英寸，故所有坐标显式 /25.4。
"""
import json
import os
import urllib.request

BASE = '/Users/shawn/WorkBuddy/2026-11-13-11-37-00/cad'
PROJECT = os.path.join(BASE, 'project.json')
MODEL = os.path.join(BASE, '首层_B方案_3D概念模型.skp')
PREVIEW = os.path.join(BASE, '首层_B方案_3D预览.png')
RUBY_OUT = os.path.join(BASE, 'build_3d_generated.rb')
HOST = 'http://127.0.0.1:28080'
MM_PER_INCH = 25.4

d = json.load(open(PROJECT, encoding='utf-8'))
H = d['building']['wall_height']
DOOR_H, WIN_SILL, WIN_TOP = 2100, 900, 2400


def I(v):
    """mm -> inch（SketchUp Ruby API 内部单位）"""
    return round(v / MM_PER_INCH, 6)


MATERIALS = {
    'WALL':         [242, 237, 227, 1.0],   # 奶油白墙面
    'FLOOR_PUBLIC': [229, 213, 189, 1.0],   # 公共区浅暖米
    'FLOOR_WOOD':   [214, 174, 123, 1.0],   # 卧室浅柚木
    'FLOOR_GREY':   [201, 201, 196, 1.0],   # 厨卫浅灰地砖
    'WOOD':         [169, 116, 63, 1.0],    # 温润柚木
    'DOOR':         [176, 124, 72, 1.0],
    'FABRIC':       [239, 231, 216, 1.0],   # 米白棉麻
    'RUG':          [201, 183, 154, 1.0],
    'GREEN':        [78, 107, 74, 1.0],
    'GLASS':        [185, 211, 216, 0.35],
    'ACCENT_Y':     [217, 164, 65, 1.0],    # 芥末黄（小面积）
    'ACCENT_R':     [181, 98, 60, 1.0],     # 砖陶红
    'ACCENT_G':     [62, 91, 74, 1.0],      # 墨绿
}

boxes, cyls, texts = [], [], []


def add_box(x0, y0, x1, y1, z0, z1, mat, name, tag, rot=None):
    b = [I(x0), I(y0), I(x1), I(y1), I(z0), I(z1), mat, name, tag]
    b.append([I(rot[0]), I(rot[1]), rot[2]] if rot else None)
    boxes.append(b)


def add_cyl(cx, cy, r, z0, z1, mat, name, tag):
    cyls.append([I(cx), I(cy), I(r), I(z0), I(z1), mat, name, tag])


def floor_mat(name):
    if '柚木' in name:
        return 'FLOOR_WOOD'
    if '灰' in name:
        return 'FLOOR_GREY'
    return 'FLOOR_PUBLIC'


# ---------------------------------------------------------------- 地面
# 整层底板，避免各分区之间的缝隙；各房间再用 8mm 薄色块区分
add_box(240, 240, 9360, 11760, -80, 0, 'FLOOR_PUBLIC', '首层地面底板', 'FLOOR')
for room in d['rooms']:
    if room.get('open'):
        # 开放书房与客厅同属公共区，只用一块极薄地毯示意范围，不设任何隔墙
        x0, y0, x1, y1 = room['zone']
        add_box(x0, y0, x1, y1, 0, 8, 'RUG', '开放书房区域地毯', 'FLOOR')
    else:
        x0, y0, x1, y1 = room['zone']
        add_box(x0, y0, x1, y1, 0, 8, floor_mat(room['floor']),
                '地面·' + room['name'], 'FLOOR')
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        texts.append([I(cx), I(cy), I(1400), room['name']])

# ---------------------------------------------------------------- 墙体
# 把每道墙的「门洞 + 窗洞」按主轴切分，实心段全高、洞口段补上下过梁
windows_by_wall = {}
for win in d['windows']:
    for w in d['walls']:
        if (w['axis'] == win['axis'] and w['lo'] == win['lo'] and w['hi'] == win['hi']
                and w['from'] <= win['from'] and win['to'] <= w['to']):
            windows_by_wall.setdefault(w['id'], []).append((win['from'], win['to'], win['id']))

door_ranges = {(x['a'], x['b']): x for x in d['doors']}

for w in d['walls']:
    axis, lo, hi, a, b = w['axis'], w['lo'], w['hi'], w['from'], w['to']
    mid = (lo + hi) / 2
    cuts = [(x[0], x[1], 'door', w['id']) for x in w.get('holes', [])]
    cuts += [(x[0], x[1], 'window', x[2]) for x in windows_by_wall.get(w['id'], [])]
    cuts.sort(key=lambda c: c[0])

    def seg(u, v, z0, z1, mat, name, tag):
        if v - u < 1 or z1 - z0 < 1:
            return
        if axis == 'h':
            add_box(u, lo, v, hi, z0, z1, mat, name, tag)
        else:
            add_box(lo, u, hi, v, z0, z1, mat, name, tag)

    def leaf(u, v, z0, z1, name, inward, double=False):
        dr = door_ranges.get((u, v))
        if dr:
            inward = dr.get('inward', inward)
            double = dr.get('double', double)
            name = dr['id'] + ' ' + dr['note']
        if axis == 'h':
            if double:
                half = (v - u) / 2
                add_box(u, mid - 20, u + half, mid + 20, z0, z1,
                        'DOOR', name + ' 左扇', 'DOOR', rot=(u, mid, 26))
                add_box(u + half, mid - 20, v, mid + 20, z0, z1,
                        'DOOR', name + ' 右扇', 'DOOR', rot=(v, mid, -26))
            else:
                add_box(u, mid - 20, v, mid + 20, z0, z1,
                        'DOOR', name, 'DOOR', rot=(u, mid, 30 * (-1 if inward < 0 else 1)))
        else:
            add_box(mid - 20, u, mid + 20, v, z0, z1,
                    'DOOR', name, 'DOOR', rot=(mid, u, -30 * (-1 if inward < 0 else 1)))

    cursor = a
    for hs, he, kind, ref in cuts:
        if hs > cursor:
            seg(cursor, hs, 0, H, 'WALL', w['id'] + ' 实墙', 'WALL')
        if kind == 'door':
            seg(hs, he, DOOR_H, H, 'WALL', w['id'] + ' 门洞过梁', 'WALL')
            leaf(hs, he, 0, DOOR_H, w['id'] + ' 门扇', 1)
        else:
            seg(hs, he, 0, WIN_SILL, 'WALL', ref + ' 窗台墙', 'WALL')
            seg(hs, he, WIN_TOP, H, 'WALL', ref + ' 窗洞过梁', 'WALL')
            if axis == 'h':
                add_box(hs, mid - 10, he, mid + 10, WIN_SILL, WIN_TOP,
                        'GLASS', ref + ' 玻璃', 'WINDOW')
            else:
                add_box(mid - 10, hs, mid + 10, he, WIN_SILL, WIN_TOP,
                        'GLASS', ref + ' 玻璃', 'WINDOW')
        cursor = max(cursor, he)
    if cursor < b:
        seg(cursor, b, 0, H, 'WALL', w['id'] + ' 实墙', 'WALL')

# ---------------------------------------------------------------- 楼梯
st = d['stair']
x0, x1, y0, n = st['x0'], st['x1'], st['y0'], st['count']
y1, dy, dz = 11640, (11640 - y0) / n, H / n
for i in range(n):
    add_box(x0, y0 + i * dy, x1, y0 + (i + 1) * dy, 0, (i + 1) * dz,
            'WOOD', '楼梯 踏步%02d' % (i + 1), 'STAIR')

# ---------------------------------------------------------------- 家具
# primitives 是平面轮廓；按 C4 注释与类型给高度/材质，做成简化体块
accent_toggle = 0
for idx, it in enumerate(d['primitives']):
    op, note = it['op'], it.get('note', '')
    if op == 'rect':
        x0, y0, x1, y1 = it['p']
        if '书架' in note:
            h, mat = 1200, 'WOOD'
        elif '书桌' in note:
            h, mat = 750, 'WOOD'
        elif (x1 - x0) > 1400 or (y1 - y0) > 1400:
            h, mat = 500, 'FABRIC'       # 床 / 大面积软装
        else:
            h, mat = 450, 'WOOD'
        name = note or ('家具%02d' % idx)
        add_box(x0, y0, x1, y1, 8, 8 + h, mat, name, 'FURN')
    elif op == 'circle':
        cx, cy, r = it['p'][0], it['p'][1], it['r']
        if '地毯' in note:
            h, mat = 24, 'RUG'
        elif '绿植' in note:
            h, mat = 650, 'GREEN'
        elif '单椅' in note:
            h, mat = 450, ('ACCENT_Y' if accent_toggle == 0 else 'ACCENT_R')
            accent_toggle += 1
        else:
            h, mat = 450, 'FABRIC'
        name = note or ('圆几/椅%02d' % idx)
        add_cyl(cx, cy, r, 8, 8 + h, mat, name, 'FURN')
    # line / arc / text / dashed_rect 为 2D 注释，3D 不生成

payload = {
    'materials': MATERIALS,
    'boxes': boxes,
    'cyls': cyls,
    'texts': texts,
    'save_path': MODEL,
    'image_path': PREVIEW,
    'mm_per_inch': MM_PER_INCH,
    # SketchUp 2027 在 Ruby 子线程调用 Model#save 后曾导致进程退出，
    # 故默认只建模+导出预览，保存请在 SketchUp 内 Cmd+S（或把此开关置 True 冒险自动存）。
    'auto_save': False,
    'meta': {
        'plan': d['plan'], 'plan_title': d['plan_title'],
        'outer_mm': d['building']['outer'], 'wall_height_mm': H,
        'room_count': len(d['rooms']), 'wall_count': len(d['walls']),
        'door_count': len(d['doors']), 'window_count': len(d['windows']),
        'style': d['style']['name'],
    },
}

RUBY = r'''require 'json'
payload = JSON.parse(<<'__SU_MCP_DATA__')
__PAYLOAD__
__SU_MCP_DATA__

m = Sketchup.active_model
result = nil
begin
  m.options["UnitsOptions"]["LengthUnit"] = 2   # 显示单位：毫米
  m.start_operation('B方案 3D 概念建模', true)
  m.entities.clear!                              # 移除模板人物组件

  mats = {}
  payload['materials'].each do |k, v|
    mat = m.materials.add(k)
    mat.color = Sketchup::Color.new(v[0], v[1], v[2])
    mat.alpha = v[3]
    mats[k] = mat
  end

  layers = {}
  ['WALL','FLOOR','DOOR','WINDOW','STAIR','FURN','TEXT'].each do |n|
    begin
      layers[n] = m.layers.add(n)
    rescue Exception
      begin
        layers[n] = m.layers[n]
      rescue Exception
        layers[n] = nil
      end
    end
  end

  up = Geom::Vector3d.new(0, 0, 1)
  payload['boxes'].each do |b|
    x0, y0, x1, y1, z0, z1 = b[0, 6]
    next if (x1 - x0).abs < 1e-6 || (y1 - y0).abs < 1e-6 || (z1 - z0).abs < 1e-6
    g = m.entities.add_group
    f = g.entities.add_face([
      Geom::Point3d.new(x0, y0, z0), Geom::Point3d.new(x1, y0, z0),
      Geom::Point3d.new(x1, y1, z0), Geom::Point3d.new(x0, y1, z0)
    ])
    # z=0 平面上的面法线可能为 -Z，按符号决定 pushpull 方向，保证始终向上拉伸
    nz = f.normal.z
    f.pushpull((z1 - z0) * (nz < 0 ? -1 : 1))
    g.material = mats[b[6]] if mats[b[6]]
    g.name = b[7].to_s
    begin
      g.layer = layers[b[8]] if layers[b[8]]
    rescue Exception
    end
    if b[9].is_a?(Array)
      px, py, deg = b[9]
      g.transform!(Geom::Transformation.rotation(
        Geom::Point3d.new(px, py, z0), up, deg * Math::PI / 180.0))
    end
  end

  payload['cyls'].each do |c|
    cx, cy, r, z0, z1 = c[0, 5]
    next if r <= 0 || z1 <= z0
    g = m.entities.add_group
    edges = g.entities.add_circle(Geom::Point3d.new(cx, cy, z0), up, r)
    f = g.entities.add_face(edges)
    nz = f.normal.z
    f.pushpull((z1 - z0) * (nz < 0 ? -1 : 1))
    g.material = mats[c[5]] if mats[c[5]]
    g.name = c[6].to_s
    begin
      g.layer = layers[c[7]] if layers[c[7]]
    rescue Exception
    end
  end

  label_ok = 0
  payload['texts'].each do |t|
    begin
      m.entities.add_text(t[3], Geom::Point3d.new(t[0], t[1], t[2]))
      label_ok += 1
    rescue Exception
    end
  end

  m.commit_operation

  view = m.active_view
  view.zoom_extents
  begin
    # 轴测相机：从东南上方俯视，突出公共区通透感
    view.camera.perspective = true
    view.camera.set(Geom::Point3d.new(560, -430, 470),
                    Geom::Point3d.new(190, 236, 55), up)
  rescue Exception
  end
  begin
    view.write_image(payload['image_path'], 1600, 1000, true)
  rescue Exception
  end
  # SketchUp 2027 移除了 Model#save_as；且经实测在 Ruby 子线程调用
  # Model#save 后进程会退出，故默认不自动保存，交还给用户在 SketchUp 内 Cmd+S。
  saved = 'AUTO_SAVE_DISABLED (请在 SketchUp 内 Cmd+S 保存)'
  if payload['auto_save']
    begin
      m.save(payload['save_path'])
      saved = payload['save_path']
    rescue Exception => e
      saved = 'SAVE_FAILED: ' + e.message
    end
  end

  bb = Geom::BoundingBox.new
  m.entities.each { |e| bb.add(e.bounds) rescue nil }
  k = payload['mm_per_inch']
  result = {
    ok: true, saved: saved, image: payload['image_path'],
    entities: m.entities.length,
    boxes: payload['boxes'].length, cyls: payload['cyls'].length,
    labels: label_ok, meta: payload['meta'],
    bounds_mm: [(bb.width * k).round, (bb.height * k).round, (bb.depth * k).round]
  }
rescue Exception => e
  begin
    m.abort_operation
  rescue Exception
  end
  result = { ok: false, error: "#{e.class}: #{e.message}",
             backtrace: (e.backtrace || []).first(4) }
end
result.to_json
'''.replace('__PAYLOAD__', json.dumps(payload, ensure_ascii=False, indent=1))

open(RUBY_OUT, 'w', encoding='utf-8').write(RUBY)
print('几何统计: %d boxes / %d cyls / %d 文字 / %d 墙 / %d 房间'
      % (len(boxes), len(cyls), len(texts), len(d['walls']), len(d['rooms'])))
print('Ruby 脚本:', RUBY_OUT, '(%d 字节)' % len(RUBY.encode('utf-8')))

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
req = urllib.request.Request(
    HOST + '/ruby/execute',
    data=json.dumps({'code': RUBY}).encode('utf-8'),
    method='POST', headers={'Content-Type': 'application/json'})
with opener.open(req, timeout=150) as resp:
    reply = json.loads(resp.read().decode('utf-8'))
print('\n=== SketchUp 返回 ===')
print(json.dumps(reply, ensure_ascii=False)[:2000])
