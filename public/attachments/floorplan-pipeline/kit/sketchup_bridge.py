#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
零依赖 SketchUp MCP stdio 桥（纯 Python 标准库，不需要 uv / mcp / httpx）

背景：官方 Tarkiin/SketchUp-MCP 的 Python server 需要联网安装 mcp、httpx 等依赖，
本机 uv sync 长时间无响应，因此提供一个等价的最小实现作为兜底。
Ruby 插件仍使用官方版本（已部署到 SketchUp 2027 的 Plugins 目录），
本脚本只负责把 MCP 的 tools/call 转成 Ruby 插件的 HTTP 请求。

端口：默认 28080。8080 被用户自有服务占用、8090 被 Docker 占用，故三处统一改为 28080
       （Python 本文件、Ruby PORT、官方 server.py 的 SKETCHUP_HOST）。
安全：Ruby 插件只绑定 127.0.0.1；execute_ruby 是官方插件提供的能力，可执行任意 Ruby，
       无沙箱，使用前请自行审阅代码并备份 .skp 模型。
"""
import json
import os
import sys
import urllib.error
import urllib.request

HOST = os.environ.get('SKETCHUP_BRIDGE_HOST', 'http://127.0.0.1:28080')

# 本机若设置了 http_proxy/HTTP_PROXY，urllib 会把 127.0.0.1 的请求也发给代理，
# 导致 502。这里显式使用空 ProxyHandler，保证直连 SketchUp 的本地 Ruby 服务。
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def log(*args):
    # MCP stdio 的 stdout 只能输出 JSON-RPC，日志一律走 stderr
    print('[sketchup-bridge]', *args, file=sys.stderr, flush=True)


def http(method, path, payload=None):
    url = HOST + path
    data = json.dumps(payload or {}).encode('utf-8') if method == 'POST' else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={'Content-Type': 'application/json'}
    )
    with OPENER.open(req, timeout=125) as resp:
        body = resp.read().decode('utf-8')
    return json.loads(body) if body else {}


TOOLS = [
    {
        'name': 'sketchup_ping',
        'description': '检查 SketchUp 桥接是否连通（等价于读取模型信息）',
        'inputSchema': {'type': 'object', 'properties': {}}
    },
    {
        'name': 'sketchup_model_info',
        'description': '获取当前 SketchUp 模型信息：名称、路径、单位、实体计数',
        'inputSchema': {'type': 'object', 'properties': {}}
    },
    {
        'name': 'sketchup_list_entities',
        'description': '列出模型中的面、边、组、组件实例',
        'inputSchema': {'type': 'object', 'properties': {}}
    },
    {
        'name': 'sketchup_create_box',
        'description': '在 SketchUp 中创建一个长方体（尺寸单位为 SketchUp 当前单位，建议先设为 mm）',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'width': {'type': 'number', 'description': '宽 X'},
                'depth': {'type': 'number', 'description': '深 Y'},
                'height': {'type': 'number', 'description': '高 Z'},
                'origin': {'type': 'array', 'items': {'type': 'number'},
                           'description': '起点 [x,y,z]，默认原点'},
                'layer': {'type': 'string', 'description': '图层/tag 名'},
                'name': {'type': 'string', 'description': '组名'},
                'material': {'type': 'string', 'description': '材质名'}
            },
            'required': ['width', 'depth', 'height']
        }
    },
    {
        'name': 'sketchup_execute_ruby',
        'description': '在 SketchUp 内执行任意 Ruby 代码（完整 Ruby API，能力最强，无沙箱，请审阅代码后使用）',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'code': {'type': 'string', 'description': '要执行的 Ruby 代码'}
            },
            'required': ['code']
        }
    }
]


def call_tool(name, args):
    if name in ('sketchup_ping', 'sketchup_model_info'):
        return http('GET', '/model/info')
    if name == 'sketchup_list_entities':
        return http('GET', '/model/entities')
    if name == 'sketchup_create_box':
        # Ruby 插件没有 /geometry/box 路由；改走已验证可用的 /ruby/execute，
        # 用 start_operation 包事务，保证 SketchUp 里 Cmd+Z 一次撤销。
        w, d, h = float(args['width']), float(args['depth']), float(args['height'])
        x, y, z = (args.get('origin') or [0, 0, 0])[:3]
        nm = json.dumps(args.get('name') or 'MCP_TestBox', ensure_ascii=False)
        code = (
            "m = Sketchup.active_model\n"
            "m.start_operation('MCP create_box', true)\n"
            "g = m.entities.add_group\n"
            "pts = [[%s, %s, %s], [%s, %s, %s], [%s, %s, %s], [%s, %s, %s]]\n"
            "f = g.entities.add_face(pts)\n"
            "f.pushpull(%s)\n"
            "g.name = %s\n"
            "m.commit_operation\n"
            "{name: g.name, entity_count: m.entities.length}.to_json"
        ) % (x, y, z, x + w, y, z, x + w, y + d, z, x, y + d, z, h, nm)
        return http('POST', '/ruby/execute', {'code': code})
    if name == 'sketchup_execute_ruby':
        code = args.get('code', '')
        if not code.strip():
            raise ValueError('code 不能为空')
        return http('POST', '/ruby/execute', {'code': code})
    raise ValueError('未知工具: %s' % name)


def handle(msg):
    mid = msg.get('id')
    method = msg.get('method')
    params = msg.get('params') or {}

    if method == 'initialize':
        return {
            'jsonrpc': '2.0', 'id': mid,
            'result': {
                'protocolVersion': '2024-11-05',
                'capabilities': {'tools': {}},
                'serverInfo': {'name': 'sketchup-bridge', 'version': '1.0.0'}
            }
        }
    # notification 没有 id，不回包
    if method and method.startswith('notifications/'):
        return None
    if method == 'ping':
        return {'jsonrpc': '2.0', 'id': mid, 'result': {}}
    if method == 'tools/list':
        return {'jsonrpc': '2.0', 'id': mid, 'result': {'tools': TOOLS}}
    if method == 'resources/list':
        return {'jsonrpc': '2.0', 'id': mid, 'result': {'resources': []}}
    if method == 'tools/call':
        name = params.get('name')
        args = params.get('arguments') or {}
        try:
            result = call_tool(name, args)
            return {
                'jsonrpc': '2.0', 'id': mid,
                'result': {
                    'content': [{'type': 'text',
                                 'text': json.dumps(result, ensure_ascii=False, indent=2)}],
                    'isError': False
                }
            }
        except Exception as exc:
            hint = ('连接失败：请先启动 SketchUp 2027，并在菜单 '
                    'Plugins → MCP Server → Start Server 启动 Ruby 服务；'
                    '确认端口 %s 未被占用。' % HOST)
            return {
                'jsonrpc': '2.0', 'id': mid,
                'result': {
                    'content': [{'type': 'text', 'text': '%s\n原始错误：%s' % (hint, exc)}],
                    'isError': True
                }
            }
    if mid is None:
        return None
    return {'jsonrpc': '2.0', 'id': mid,
            'error': {'code': -32601, 'message': 'Method not found: %s' % method}}


def main():
    log('启动，桥接目标', HOST)
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            log('忽略非 JSON 输入')
            continue
        resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + '\n')
            sys.stdout.flush()


if __name__ == '__main__':
    main()
