#!/usr/bin/env python3
"""derive_designs.py — S2 风格设计稿生成器（内容契约驱动）。

与「复制原型 DOM 再换色」不同：本脚本从 candidates.json 的 content_contract
读取首页必须呈现的信息项，5 个方向各自**重新构图**（布局、卡片形态、图标、
图形、装饰语言全部独立设计），只保证信息项、文案、数值、操作与 tab 不丢失。

用法：
  python3 derive_designs.py --config <candidates.json> --out <候选目录> \
      --shell <comparison-shell.html> [--verify-only]

产物：style-A..E.html、comparison.html、contract-check.json。
PNG 由外部无头浏览器渲染 .screen 元素得到（本脚本不依赖浏览器）。
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from pathlib import Path

# 自绘线性图标，非第三方素材
PATHS = {
    'users': '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3 3-5 6-5s6 2 6 5"/><path d="M16 6a3 3 0 0 1 0 6"/><path d="M18 15c2 .5 3 2 3 5"/>',
    'grid': '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    'book': '<path d="M4 5a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2z"/><path d="M8 7h8M8 11h6"/>',
    'wallet': '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18M16 14h2"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'calendar': '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    'bell': '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
    'check': '<path d="M4 12l5 5L20 6"/>',
    'arrow': '<path d="M5 12h14M13 6l6 6-6 6"/>',
    'chevron': '<path d="M9 6l6 6-6 6"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'link': '<path d="M10 13a5 5 0 0 0 7 0l2-2a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-2 2a5 5 0 0 0 7 7l1-1"/>',
    'home': '<path d="M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    'user': '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-7 8-7s8 3 8 7"/>',
}


def icon(name: str, size: int = 18, sw: float = 1.7) -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{PATHS[name]}</svg>')


def esc(s) -> str:
    return html_lib.escape(str(s), quote=False)


PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>首页设计稿 · __ID__ __NAME__</title>
<style>
:root{
__TOKENS__
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:#e8ebef;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased}
.screen{width:390px;height:820px;position:relative;margin:0 auto;overflow:hidden;display:flex;flex-direction:column;background:var(--bg);color:var(--ink)}
svg{display:block;flex:none}
button{font:inherit;cursor:pointer;border:0;background:none;color:inherit;padding:0}
__CSS__
</style></head><body>
<div class="screen" data-style="__ID__">
__BODY__
</div>
</body></html>
"""

# ---------------------------------------------------------------- A 克制账务
CSS_A = """
.hd{display:flex;align-items:center;justify-content:space-between;padding:22px 22px 15px;background:var(--surface);border-bottom:1px solid var(--line)}
.hd h1{font-size:17px;font-weight:650;margin:0;letter-spacing:.5px}
.hd .dt{font-size:11px;color:var(--muted);margin-top:3px}
.av{width:30px;height:30px;border-radius:50%;background:var(--soft);color:var(--brand-text);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;border:1px solid var(--line)}
.main{flex:1;overflow:hidden;padding:0 22px}
.hero{padding:30px 0 24px;border-bottom:1px solid var(--line)}
.hero .n{font-size:21px;font-weight:650;letter-spacing:-.4px}
.mline{display:grid;grid-template-columns:repeat(4,1fr);margin-top:26px}
.mline .m{border-left:1px solid var(--line);padding-left:10px}
.mline .m:first-child{border-left:0;padding-left:0}
.mline b{display:block;font-size:19px;font-weight:700;letter-spacing:-.5px;white-space:nowrap;font-variant-numeric:tabular-nums}
.mline span{display:block;font-size:10px;color:var(--muted);margin-top:4px;white-space:nowrap}
.sec{padding:22px 0;border-bottom:1px solid var(--line)}
.sec h2{font-size:11px;font-weight:650;color:var(--muted);letter-spacing:1.4px;margin:0 0 8px}
.row{display:flex;align-items:center;justify-content:space-between;padding:9px 0;font-size:13px}
.row .l{display:flex;align-items:center;gap:10px}
.dot{width:5px;height:5px;border-radius:50%;background:var(--line)}
.row b{font-size:14px;font-weight:650;font-variant-numeric:tabular-nums}
.qrow{display:flex;gap:16px;flex-wrap:wrap;margin-top:4px}
.qrow button{display:flex;align-items:center;gap:5px;font-size:12px;color:var(--brand-text);padding:3px 0}
.qrow svg{width:13px;height:13px}
.empty{border:1px solid var(--line);padding:16px;display:flex;align-items:center;gap:14px;margin-top:4px}
.empty>svg{width:30px;height:30px;color:var(--muted);stroke-width:1.2}
.empty .tx{font-size:13px}
.empty .go{display:inline-flex;align-items:center;gap:6px;margin-top:10px;font-size:12px;font-weight:700;color:var(--brand-text);border-bottom:1px solid var(--brand-text);padding-bottom:2px}
.empty .go svg{width:13px;height:13px}
.tabs{display:flex;border-top:1px solid var(--line);background:var(--surface);height:58px}
.tabs button{flex:1;font-size:11px;color:var(--muted);position:relative}
.tabs button.on{color:var(--brand-text);font-weight:700}
.tabs button.on::before{content:"";position:absolute;top:0;left:26%;right:26%;height:2px;background:var(--brand)}
"""

# ---------------------------------------------------------------- B 清爽课表
CSS_B = """
.hd{background:var(--brand);color:var(--brand-ink);padding:18px 20px 14px;border-bottom-left-radius:22px;border-bottom-right-radius:22px}
.hd .top{display:flex;justify-content:space-between;align-items:center}
.hd h1{font-size:18px;font-weight:700;margin:0}
.hd .dt{font-size:11px;opacity:.85;margin-top:3px}
.spark{display:flex;align-items:flex-end;gap:6px;height:32px;margin-top:14px}
.spark i{flex:1;background:rgba(255,255,255,.26);border-radius:3px 3px 0 0}
.main{flex:1;padding:14px 16px 0;overflow:hidden;background:var(--bg)}
.hi{font-size:13px;font-weight:650;margin:0 2px 12px}
.mgrid{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.mc{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:10px 12px;display:flex;gap:10px;align-items:center;box-shadow:0 1px 4px rgba(37,99,235,.06)}
.mc .ic{width:30px;height:30px;border-radius:9px;background:var(--soft);color:var(--brand);display:flex;align-items:center;justify-content:center}
.mc b{display:block;font-size:18px;font-weight:700;line-height:1.1;white-space:nowrap;font-variant-numeric:tabular-nums}
.mc span{display:block;font-size:10px;color:var(--muted);margin-top:3px;white-space:nowrap}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;margin-top:12px;padding:10px 12px}
.card h2{font-size:12px;font-weight:700;margin:0 0 4px}
.trow{display:flex;align-items:center;gap:9px;padding:8px 0;border-bottom:1px solid var(--line);font-size:12px}
.trow:last-child{border-bottom:0}
.trow .ti{width:22px;height:22px;border-radius:7px;background:var(--soft);color:var(--brand);display:flex;align-items:center;justify-content:center}
.trow .ti svg{width:13px;height:13px}
.trow .tl{flex:1}
.trow b{color:var(--brand-text);font-weight:700;white-space:nowrap}
.trow .chev{color:var(--muted)}
.trow .chev svg{width:13px;height:13px}
.qgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:8px}
.qgrid button{display:flex;flex-direction:column;align-items:center;gap:5px;font-size:10px;color:var(--ink)}
.qgrid .qi{width:40px;height:40px;border-radius:50%;background:var(--surface);border:1px solid var(--line);color:var(--brand);display:flex;align-items:center;justify-content:center}
.today{display:flex;align-items:center;gap:12px;padding:6px 0}
.today .art{width:52px;height:52px;border-radius:14px;background:var(--soft);color:var(--brand);display:flex;align-items:center;justify-content:center}
.today .tx{font-size:12px;flex:1}
.today .go{display:block;background:var(--brand);color:var(--brand-ink);border-radius:9px;padding:8px 13px;font-size:12px;font-weight:700;margin-top:8px}
.tabs{height:60px;display:flex;background:var(--surface);border-top:1px solid var(--line)}
.tabs button{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;font-size:10px;color:var(--muted)}
.tabs button.on{color:var(--brand);font-weight:700}
.tabs svg{width:17px;height:17px}
"""

# ---------------------------------------------------------------- C 柔和亲和
CSS_C = """
.blob{position:absolute;border-radius:50%;pointer-events:none}
.b1{width:230px;height:230px;background:#D8EFE4;top:-100px;right:-80px;opacity:.65}
.b2{width:170px;height:170px;background:#E9F5DE;bottom:110px;left:-90px;opacity:.6}
.hd{padding:26px 24px 8px;display:flex;justify-content:space-between;align-items:flex-start;position:relative}
.hd h1{font-size:12px;font-weight:600;color:var(--muted);margin:0}
.hd .big{font-size:23px;font-weight:700;margin-top:9px;letter-spacing:-.6px}
.hd .dt{font-size:11px;color:var(--muted);margin-top:5px}
.av2{width:44px;height:44px;border-radius:16px;background:var(--surface);box-shadow:0 6px 18px rgba(47,110,90,.12);display:flex;align-items:center;justify-content:center;color:var(--brand-text);font-size:16px;font-weight:700}
.main{flex:1;padding:8px 20px 0;position:relative;overflow:hidden}
.hero{background:var(--surface);border-radius:26px;padding:17px 20px;box-shadow:0 8px 24px rgba(47,110,90,.10);position:relative}
.hero .lb{font-size:11px;color:var(--muted)}
.hero .money{font-size:33px;font-weight:700;letter-spacing:-1.2px;margin-top:2px;font-variant-numeric:tabular-nums}
.chips{display:flex;gap:6px;margin-top:14px;flex-wrap:wrap}
.chip{background:var(--soft);border-radius:14px;padding:6px 10px;font-size:10px;display:flex;gap:5px;align-items:center;white-space:nowrap}
.chip b{font-weight:700;font-size:12px}
.h2{font-size:12px;font-weight:700;margin:15px 2px 9px;position:relative}
.tgrid{display:grid;grid-template-columns:1fr 1fr;gap:9px;position:relative}
.tc{background:var(--surface);border-radius:20px;padding:10px 13px;box-shadow:0 4px 14px rgba(47,110,90,.07)}
.tc b{display:block;font-size:18px;font-weight:700;color:var(--brand-text);font-variant-numeric:tabular-nums}
.tc span{display:block;font-size:10px;color:var(--muted);margin-top:3px}
.qrow{display:flex;gap:7px;flex-wrap:wrap;position:relative}
.qrow button{background:var(--surface);border-radius:20px;padding:8px 12px;font-size:11px;box-shadow:0 3px 10px rgba(47,110,90,.07)}
.emptyc{background:var(--surface);border-radius:22px;padding:12px;display:flex;align-items:center;gap:12px;box-shadow:0 4px 14px rgba(47,110,90,.07);position:relative}
.emptyc .art{width:48px;height:48px;border-radius:18px;background:var(--soft);color:var(--brand-text);display:flex;align-items:center;justify-content:center}
.emptyc .tx{font-size:12px;flex:1}
.emptyc .go{display:block;background:var(--brand);color:#fff;border-radius:16px;padding:8px 14px;font-size:12px;font-weight:700;margin-top:8px;box-shadow:0 4px 0 rgba(47,110,90,.25)}
.tabs{margin:0 16px 14px;height:56px;background:var(--surface);border-radius:22px;display:flex;box-shadow:0 6px 20px rgba(47,110,90,.14);position:relative}
.tabs button{flex:1;font-size:10px;color:var(--muted);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px}
.tabs button.on{color:var(--brand-text);font-weight:700}
.tabs svg{width:16px;height:16px}
"""

# ---------------------------------------------------------------- D 深墨数据
CSS_D = """
.hd{padding:20px 22px 0;display:flex;justify-content:space-between;align-items:center}
.hd h1{font-size:12px;font-weight:600;color:var(--muted);margin:0;letter-spacing:1.4px}
.hd .dt{font-size:11px;color:var(--muted)}
.main{flex:1;padding:0 22px;overflow:hidden}
.hero{margin-top:18px}
.hero .lb{font-size:11px;color:var(--muted);letter-spacing:1.2px}
.hero .money{font-size:42px;font-weight:700;color:var(--brand);letter-spacing:-2px;line-height:1.1;margin-top:5px;font-variant-numeric:tabular-nums}
.hero .cap{font-size:11px;color:var(--muted);margin-top:3px}
.sparkline{margin-top:12px;width:100%;height:38px}
.m3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:16px}
.m3 .mc{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:10px}
.m3 b{display:block;font-size:20px;font-weight:700;font-variant-numeric:tabular-nums}
.m3 span{display:block;font-size:10px;color:var(--muted);margin-top:3px;white-space:nowrap}
.sec{margin-top:20px}
.sec h2{font-size:11px;color:var(--muted);letter-spacing:1.4px;margin:0 0 7px;font-weight:600}
.trow{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--line);font-size:12px}
.trow .bar{width:3px;height:16px;background:var(--line);border-radius:2px}
.trow.hot .bar{background:var(--brand)}
.trow .tl{flex:1}
.trow b{font-variant-numeric:tabular-nums;font-weight:700;white-space:nowrap}
.trow.hot b{color:var(--brand)}
.qrow{display:flex;gap:7px;flex-wrap:wrap}
.qrow button{border:1px solid var(--line);background:var(--surface);border-radius:5px;padding:7px 10px;font-size:11px;color:var(--ink)}
.empty{display:flex;align-items:center;gap:12px;border:1px dashed var(--line);border-radius:6px;padding:13px;margin-top:4px}
.empty>svg{color:var(--brand)}
.empty .tx{font-size:12px;flex:1}
.empty .go{display:block;background:var(--brand);color:var(--brand-ink);border-radius:5px;padding:8px 14px;font-size:12px;font-weight:700;margin-top:8px}
.tabs{height:58px;display:flex;background:var(--surface);border-top:1px solid var(--line)}
.tabs button{flex:1;font-size:10px;color:var(--muted);position:relative}
.tabs button.on{color:var(--brand);font-weight:700}
.tabs button.on::before{content:"";position:absolute;top:0;left:28%;right:28%;height:2px;background:var(--brand);box-shadow:0 0 8px var(--brand)}
"""

# ---------------------------------------------------------------- E 活力台账
CSS_E = """
.hd{background:var(--brand);color:#1A1A1A;padding:20px 20px 16px;position:relative;overflow:hidden;border-bottom:3px solid #1A1A1A}
.hd h1{font-size:12px;font-weight:800;margin:0;letter-spacing:1.4px}
.hd .big{font-size:25px;font-weight:800;margin-top:10px;letter-spacing:-1px}
.hd .dt{font-size:11px;margin-top:5px;opacity:.75}
.mascot{position:absolute;right:20px;top:26px;width:54px;height:54px;background:#1A1A1A;border-radius:50%;display:flex;align-items:center;justify-content:center;gap:7px}
.mascot i{width:7px;height:7px;background:var(--brand);border-radius:50%}
.mascot::after{content:"";position:absolute;bottom:12px;width:20px;height:8px;border-bottom:2px solid var(--brand);border-radius:0 0 20px 20px}
.main{flex:1;padding:14px 16px 0;overflow:hidden;background:var(--bg)}
.money-card{background:#1A1A1A;color:var(--brand);border-radius:18px;padding:13px 16px;box-shadow:0 5px 0 #C9D98A}
.money-card .lb{font-size:10px;opacity:.85}
.money-card .v{font-size:32px;font-weight:800;letter-spacing:-1.5px;line-height:1.15;font-variant-numeric:tabular-nums}
.stickers{display:flex;gap:7px;margin-top:11px;flex-wrap:wrap}
.stickers .s{background:var(--surface);border:2px solid #1A1A1A;border-radius:14px;padding:6px 10px;font-size:10px;box-shadow:0 3px 0 #1A1A1A;transform:rotate(-2deg);white-space:nowrap}
.stickers .s:nth-child(2){transform:rotate(1.5deg)}
.stickers .s:nth-child(3){transform:rotate(-1deg)}
.stickers b{font-size:14px;font-weight:800}
.h2{font-size:12px;font-weight:800;margin:15px 2px 8px}
.box{background:var(--surface);border:2px solid #1A1A1A;border-radius:16px;padding:8px 13px;box-shadow:0 4px 0 #1A1A1A}
.trow{display:flex;justify-content:space-between;padding:6px 0;border-bottom:2px dotted var(--line);font-size:12px;gap:8px}
.trow:last-child{border-bottom:0}
.trow b{font-weight:800;white-space:nowrap}
.qgrid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.qgrid button{background:var(--brand);color:#1A1A1A;border:2px solid #1A1A1A;border-radius:14px;padding:9px;font-size:11px;font-weight:800;box-shadow:0 3px 0 #1A1A1A}
.emptyc{display:flex;align-items:center;gap:10px}
.emptyc .art{width:42px;height:42px;border-radius:50%;background:var(--brand);border:2px solid #1A1A1A;display:flex;align-items:center;justify-content:center;flex:none}
.emptyc .tx{font-size:12px;flex:1}
.emptyc .go{display:block;background:#1A1A1A;color:var(--brand);border-radius:14px;padding:9px 14px;font-size:12px;font-weight:800;margin-top:8px;box-shadow:0 3px 0 #9AAF42}
.tabs{height:58px;display:flex;background:var(--surface);border-top:2px solid #1A1A1A}
.tabs button{flex:1;font-size:10px;font-weight:800;color:var(--muted)}
.tabs button.on{background:var(--brand);color:#1A1A1A}
"""

TAB_ICONS = ['home', 'users', 'calendar', 'book', 'user']


def tabs_html(c, with_icon=False, on_class='on'):
    out = ['<nav class="tabs">']
    for i, name in enumerate(c['tabs']):
        cls = on_class if i == 0 else ''
        ic = icon(TAB_ICONS[i], 17) if with_icon else ''
        out.append(f'<button class="{cls}">{ic}<span>{esc(name)}</span></button>')
    out.append('</nav>')
    return ''.join(out)


def body_A(c):
    m = c['metrics']
    todos = c['todos']
    parts = [
        '<header class="hd"><div><h1>' + esc(c['page_title']) + '</h1><div class="dt">' + esc(c['date']) + '</div></div><div class="av">师</div></header>',
        '<main class="main">',
        '<section class="hero"><div class="n">' + esc(c['greeting']) + '</div><div class="mline">',
    ]
    for x in m:
        parts.append(f'<div class="m"><b>{esc(x["value"])}</b><span>{esc(x["label"])}</span></div>')
    parts.append('</div></section>')
    parts.append('<section class="sec"><h2>' + esc(c['todo_section']) + '</h2>')
    for t in todos:
        parts.append(f'<div class="row"><div class="l"><i class="dot"></i><span>{esc(t["label"])}</span></div><b>{esc(t["value"])}</b></div>')
    parts.append('</section>')
    parts.append('<section class="sec"><h2>' + esc(c['quick_section']) + '</h2><div class="qrow">')
    for q in c['quick']:
        parts.append(f'<button>{icon("plus", 13)}<span>{esc(q)}</span></button>')
    parts.append('</div></section>')
    parts.append('<section class="sec"><h2>' + esc(c['today_section']) + '</h2><div class="empty">' + icon('calendar', 30, 1.2) +
                '<div><div class="tx">' + esc(c['empty']) + '</div><button class="go">' + esc(c['primary_action']) + icon('arrow', 13) + '</button></div></div></section>')
    parts.append('</main>' + tabs_html(c))
    return ''.join(parts)


def body_B(c):
    bars = [10, 18, 12, 24, 16, 28, 14]
    parts = [
        '<header class="hd"><div class="top"><div><h1>' + esc(c['page_title']) + '</h1><div class="dt">' + esc(c['date']) + '</div></div>' + icon('bell', 20) + '</div><div class="spark">',
        ''.join(f'<i style="height:{h}px"></i>' for h in bars), '</div></header>',
        '<main class="main"><div class="hi">' + esc(c['greeting']) + '</div><div class="mgrid">',
    ]
    for x in c['metrics']:
        parts.append(f'<div class="mc"><div class="ic">{icon(x["icon"], 17)}</div><div><b>{esc(x["value"])}</b><span>{esc(x["label"])}</span></div></div>')
    parts.append('</div>')
    parts.append('<section class="card"><h2>' + esc(c['todo_section']) + '</h2>')
    for t in c['todos']:
        parts.append(f'<div class="trow"><div class="ti">{icon("check", 13)}</div><span class="tl">{esc(t["label"])}</span><b>{esc(t["value"])}</b><span class="chev">{icon("chevron", 13)}</span></div>')
    parts.append('</section>')
    parts.append('<section class="card"><h2>' + esc(c['quick_section']) + '</h2><div class="qgrid">')
    for i, q in enumerate(c['quick']):
        parts.append(f'<button><span class="qi">{icon(["plus","grid","book","wallet"][i], 18)}</span><span>{esc(q)}</span></button>')
    parts.append('</div></section>')
    parts.append('<section class="card"><h2>' + esc(c['today_section']) + '</h2><div class="today"><div class="art">' + icon('calendar', 26, 1.4) +
                '</div><div class="tx">' + esc(c['empty']) + '<button class="go">' + esc(c['primary_action']) + '</button></div></div></section>')
    parts.append('</main>' + tabs_html(c, with_icon=True))
    return ''.join(parts)


def body_C(c):
    parts = [
        '<div class="blob b1"></div><div class="blob b2"></div>',
        '<header class="hd"><div><h1>' + esc(c['page_title']) + '</h1><div class="big">' + esc(c['greeting']) +
        '</div><div class="dt">' + esc(c['date']) + '</div></div><div class="av2">师</div></header>',
        '<main class="main"><section class="hero"><div class="lb">' + esc(c['metrics'][3]['label']) +
        '</div><div class="money">' + esc(c['metrics'][3]['value']) + '</div><div class="chips">',
    ]
    for x in c['metrics'][:3]:
        parts.append(f'<span class="chip"><b>{esc(x["value"])}</b>{esc(x["label"])}</span>')
    parts.append('</div></section>')
    parts.append('<div class="h2">' + esc(c['todo_section']) + '</div><div class="tgrid">')
    for t in c['todos']:
        parts.append(f'<div class="tc"><b>{esc(t["value"])}</b><span>{esc(t["label"])}</span></div>')
    parts.append('</div>')
    parts.append('<div class="h2">' + esc(c['quick_section']) + '</div><div class="qrow">')
    for q in c['quick']:
        parts.append(f'<button>{esc(q)}</button>')
    parts.append('</div>')
    parts.append('<div class="h2">' + esc(c['today_section']) + '</div><div class="emptyc"><div class="art">' + icon('calendar', 24, 1.5) +
                '</div><div class="tx">' + esc(c['empty']) + '<button class="go">' + esc(c['primary_action']) + '</button></div></div>')
    parts.append('</main>' + tabs_html(c, with_icon=True))
    return ''.join(parts)


def body_D(c):
    parts = [
        '<header class="hd"><h1>' + esc(c['page_title']) + '</h1><div class="dt">' + esc(c['date']) + '</div></header>',
        '<main class="main"><section class="hero"><div class="lb">' + esc(c['greeting']) + '</div><div class="money">' + esc(c['metrics'][3]['value']) +
        '</div><div class="cap">' + esc(c['metrics'][3]['label']) + '</div>',
        '<svg class="sparkline" viewBox="0 0 340 38" preserveAspectRatio="none"><polyline points="0,30 40,26 80,29 120,18 160,22 200,12 240,16 280,7 340,10" fill="none" stroke="var(--brand)" stroke-width="2" stroke-linejoin="round"/><polyline points="0,30 40,26 80,29 120,18 160,22 200,12 240,16 280,7 340,10 340,38 0,38" fill="var(--brand)" opacity=".10" stroke="none"/></svg></section>',
        '<div class="m3">',
    ]
    for x in c['metrics'][:3]:
        parts.append(f'<div class="mc"><b>{esc(x["value"])}</b><span>{esc(x["label"])}</span></div>')
    parts.append('</div>')
    parts.append('<section class="sec"><h2>' + esc(c['todo_section']) + '</h2>')
    for i, t in enumerate(c['todos']):
        hot = ' hot' if i in (2, 3) else ''
        parts.append(f'<div class="trow{hot}"><i class="bar"></i><span class="tl">{esc(t["label"])}</span><b>{esc(t["value"])}</b></div>')
    parts.append('</section>')
    parts.append('<section class="sec"><h2>' + esc(c['quick_section']) + '</h2><div class="qrow">')
    for q in c['quick']:
        parts.append(f'<button>{esc(q)}</button>')
    parts.append('</div></section>')
    parts.append('<section class="sec"><h2>' + esc(c['today_section']) + '</h2><div class="empty">' + icon('calendar', 26, 1.4) +
                '<div class="tx">' + esc(c['empty']) + '<button class="go">' + esc(c['primary_action']) + '</button></div></div></section>')
    parts.append('</main>' + tabs_html(c))
    return ''.join(parts)


def body_E(c):
    parts = [
        '<header class="hd"><h1>' + esc(c['page_title']) + '</h1><div class="big">' + esc(c['greeting']) +
        '</div><div class="dt">' + esc(c['date']) + '</div><div class="mascot"><i></i><i></i></div></header>',
        '<main class="main"><section class="money-card"><div class="lb">' + esc(c['metrics'][3]['label']) +
        '</div><div class="v">' + esc(c['metrics'][3]['value']) + '</div></section><div class="stickers">',
    ]
    for x in c['metrics'][:3]:
        parts.append(f'<span class="s"><b>{esc(x["value"])}</b> {esc(x["label"])}</span>')
    parts.append('</div>')
    parts.append('<div class="h2">' + esc(c['todo_section']) + '</div><div class="box">')
    for t in c['todos']:
        parts.append(f'<div class="trow"><span>{esc(t["label"])}</span><b>{esc(t["value"])}</b></div>')
    parts.append('</div>')
    parts.append('<div class="h2">' + esc(c['quick_section']) + '</div><div class="qgrid">')
    for q in c['quick']:
        parts.append(f'<button>{esc(q)}</button>')
    parts.append('</div>')
    parts.append('<div class="h2">' + esc(c['today_section']) + '</div><div class="emptyc"><div class="art">' + icon('calendar', 22, 2) +
                '</div><div class="tx">' + esc(c['empty']) + '<button class="go">' + esc(c['primary_action']) + '</button></div></div>')
    parts.append('</main>' + tabs_html(c))
    return ''.join(parts)


DESIGNS = [
    ('A', CSS_A, body_A),
    ('B', CSS_B, body_B),
    ('C', CSS_C, body_C),
    ('D', CSS_D, body_D),
    ('E', CSS_E, body_E),
]


def flatten_contract(c):
    items = [c['page_title'], c['greeting'], c['date'], c['todo_section'],
             c['quick_section'], c['today_section'], c['empty'], c['primary_action']]
    for m in c['metrics']:
        items += [m['value'], m['label']]
    for t in c['todos']:
        items += [t['label'], t['value']]
    items += list(c['quick']) + list(c['tabs'])
    # 去重但保留顺序
    seen, out = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def visible_text(page_html):
    body = page_html.split('<body>')[-1]
    return html_lib.unescape(re.sub(r'<[^>]+>', ' ', body))


def verify_contract(pages, c):
    required = flatten_contract(c)
    errors, per = [], {}
    for cid, html_text in pages.items():
        text = visible_text(html_text)
        missing = [x for x in required if x not in text]
        buttons = ' '.join(html_lib.unescape(re.sub(r'<[^>]+>', ' ', b))
                           for b in re.findall(r'<button[^>]*>.*?</button>', html_text, re.S))
        missing_actions = [a for a in ([c['primary_action']] + list(c['quick'])) if a not in buttons]
        nav = ' '.join(re.findall(r'<nav[^>]*>.*?</nav>', html_text, re.S))
        missing_tabs = [t for t in c['tabs'] if t not in html_lib.unescape(re.sub(r'<[^>]+>', ' ', nav))]
        # 设计图不得出现原型评审道具文案
        forbidden = [x for x in ('演示数据', '原型 v1.5', 'PRD v1.0', '非真实个人信息') if x in text]
        per[cid] = {
            'required_items': len(required),
            'missing_text': missing,
            'missing_actions': missing_actions,
            'missing_tabs': missing_tabs,
            'prototype_chrome_leaked': forbidden,
        }
        for k in ('missing_text', 'missing_actions', 'missing_tabs', 'prototype_chrome_leaked'):
            if per[cid][k]:
                errors.append(f'{cid}: {k} = {per[cid][k]}')
    return {
        'ok': not errors,
        'contract_source': c['source'],
        'required_items': required,
        'per_candidate': per,
        'errors': errors,
        'note': '校验对象是信息契约，不是 DOM 结构；设计稿允许并应当重新构图',
    }


def build_comparison(shell, cfg):
    scale = float(cfg.get('scale', 0.55))
    vw, vh = round(390 * scale), round(820 * scale)
    colmin = vw + 32
    s = shell
    s = re.sub(r'<h1>.*?</h1>', lambda m: f'<h1>{esc(cfg["title"])}</h1>', s, count=1)
    s = re.sub(r'<p class="lead">.*?</p>', lambda m: f'<p class="lead">{esc(cfg["lead"])}</p>', s, count=1, flags=re.S)
    s = re.sub(r'\.grid \{[^}]*\}', lambda m: f'.grid {{ display:grid; grid-template-columns:repeat({len(cfg["candidates"])},minmax({colmin}px,1fr)); gap:16px; align-items:start; }}', s, count=1)
    s = re.sub(r'\.stage \{[^}]*\}', lambda m: '.stage { padding:8px; display:flex; justify-content:center; background:var(--bg); }', s, count=1)
    iframe_css = (f'.stage .viewport {{ width:{vw}px; height:{vh}px; overflow:hidden; }}\n'
                  f'  .stage .frame {{ width:390px; height:820px; transform:scale({scale}); transform-origin:top left; }}\n'
                  f'  .stage iframe {{ width:390px; height:820px; border:1px solid var(--line); border-radius:8px; background:#fff; }}')
    s = re.sub(r'\.stage iframe \{[^}]*\}', lambda m: iframe_css, s, count=1)
    s = re.sub(r'body \{[^}]*\}', lambda m: m.group(0).replace('margin:0;', 'margin:0;overflow-x:auto;'), s, count=1)

    cols = []
    for c in cfg['candidates']:
        cid = c['id']
        cols.append(f'''    <section class="col">
      <header><h2>{esc(cid)} · {esc(c["name"])}</h2><div class="tagline">{esc(c["tagline"])}</div></header>
      <div class="stage"><div class="viewport"><div class="frame"><iframe src="style-{esc(cid)}.html" title="风格 {esc(cid)} 首页设计稿"></iframe></div></div></div>
      <div class="notes">
        <p><b>适用场景：</b>{esc(c["scenario"])}</p>
        <p><b>代价：</b>{esc(c["cost"])}</p>
        <p><b>已知风险：</b>{esc(c["risk"])}</p>
        <p><a href="style-{esc(cid)}.png" target="_blank">查看全尺寸 PNG</a> · <a href="style-{esc(cid)}.tokens.json" target="_blank">token 快照</a></p>
      </div>
    </section>''')
    grid_start = s.find('<div class="grid">')
    footer_start = s.find('<footer>')
    if grid_start < 0 or footer_start < 0:
        raise ValueError('comparison-shell.html 结构不符合预期')
    s = s[:grid_start] + '<div class="grid">\n' + '\n'.join(cols) + '\n  </div>\n\n  ' + s[footer_start:]
    s = re.sub(r'<footer>.*?</footer>', lambda m: f'<footer>{esc(cfg["footer"])}</footer>', s, count=1, flags=re.S)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--shell', default=str(Path(__file__).resolve().parent.parent / 'assets/comparison-shell.html'))
    ap.add_argument('--verify-only', action='store_true')
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding='utf-8'))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    contract = cfg['content_contract']
    by_id = {c['id']: c for c in cfg['candidates']}

    if not args.verify_only:
        for cid, css, fn in DESIGNS:
            cand = by_id[cid]
            tokens = '\n'.join(f'  {k}: {v};' for k, v in cand['vars'].items())
            page = (PAGE.replace('__TOKENS__', tokens)
                        .replace('__CSS__', css)
                        .replace('__BODY__', fn(contract))
                        .replace('__ID__', cid)
                        .replace('__NAME__', cand['name']))
            (out / f'style-{cid}.html').write_text(page, encoding='utf-8')
            (out / f'style-{cid}.tokens.json').write_text(
                json.dumps(cand['tokens'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        shell = Path(args.shell).read_text(encoding='utf-8')
        (out / 'comparison.html').write_text(build_comparison(shell, cfg), encoding='utf-8')

    pages = {p.stem.replace('style-', ''): p.read_text(encoding='utf-8')
             for p in sorted(out.glob('style-?.html'))}
    report = verify_contract(pages, contract)
    (out / 'contract-check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': report['ok'], 'candidates': sorted(pages),
                      'required_items': len(report['required_items']),
                      'errors': report['errors']}, ensure_ascii=False, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
