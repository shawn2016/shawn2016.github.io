#!/usr/bin/env python3
"""
Firefly 加密页密码构建期注入脚本。

仓库中 posts 的 frontmatter 只存占位符 __NOTE_PASSWORD__，
构建前由 CI Secret（NOTE_PASSWORD）或本地环境变量替换为真实密码，
构建后 --restore 还原占位符——密码永远不进仓库。

只作用于 frontmatter 的 `password:` 行，不碰正文。

用法：
  NOTE_PASSWORD=xxx python3 inject_password.py            # 注入
  NOTE_PASSWORD=xxx python3 inject_password.py --restore  # 还原（构建后）
"""
import os
import re
import sys
from pathlib import Path

PLACEHOLDER = "__NOTE_PASSWORD__"
POSTS_DIR = Path(__file__).resolve().parent / "src" / "content" / "posts"


def main():
    pw = os.environ.get("NOTE_PASSWORD", "")
    restore = "--restore" in sys.argv
    if not pw:
        sys.exit("[错误] 需要 NOTE_PASSWORD 环境变量")

    src = PLACEHOLDER if not restore else pw
    dst = pw if not restore else PLACEHOLDER
    pattern = re.compile(r"^(password\s*:\s*)(.+)$", re.M)

    hits = 0
    for p in POSTS_DIR.rglob("*.md"):
        text = p.read_text(encoding="utf-8")
        if src not in text:
            continue
        new_text, n = pattern.subn(lambda m: m.group(1) + f'"{dst}"', text)
        if n:
            p.write_text(new_text, encoding="utf-8")
            hits += 1
    print(f"[{'还原' if restore else '注入'}] 处理了 {hits} 个加密文件（password 行）")
    if not hits:
        print(f"[提示] 未找到含目标字符串的 password 行: {src[:8]}…")


if __name__ == "__main__":
    main()
