#!/bin/bash
# 本地构建 + 预览一键脚本
# 用法: ./build-local.sh [密码]     不传密码则用占位符构建
set -e
cd "$(dirname "$0")"

PW="${1:-}"
if [ -n "$PW" ]; then
  NOTE_PASSWORD="$PW" python3 inject_password.py
fi

pnpm build

if [ -n "$PW" ]; then
  NOTE_PASSWORD="$PW" python3 inject_password.py --restore
  echo "[安全] 占位符已还原"
fi

echo "构建完成 → dist/  启动预览: pnpm preview"
