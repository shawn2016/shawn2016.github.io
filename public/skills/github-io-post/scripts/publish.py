#!/usr/bin/env python3
"""Publish a local directory to a GitHub repo via the Git Data API.

Why not git clone/push: shallow clones get killed by memory limits on this
machine (Exit 137). This script creates blobs, one tree based on the current
tree, a commit, then moves the branch ref.

Usage:
  python3 publish.py --dir ./site-publish --repo shawn2016/shawn2016.github.io \
      --message "feat: add post" [--branch main] [--dry-run]
"""

import argparse
import base64
import json
import subprocess
from pathlib import Path

TEXT_SUFFIXES = {".md", ".txt", ".json", ".html", ".css", ".js", ".ts", ".svg", ".py", ".yml", ".yaml"}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".woff2", ".woff", ".pdf", ".mp3", ".m4a"}


def gh(method: str, endpoint: str, payload=None, jq: str | None = None):
    cmd = ["gh", "api", endpoint, "--method", method]
    if jq:
        cmd += ["--jq", jq]
    data = None
    if payload is not None:
        cmd += ["--input", "-"]
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    proc = subprocess.run(cmd, input=data, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {method} {endpoint} failed:\n{proc.stderr.decode(errors='replace')[-800:]}")
    out = proc.stdout.decode("utf-8", errors="replace").strip()
    if not out:
        return {}
    if jq:
        return out
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"raw": out}


def collect(root: Path):
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(p.startswith(".") for p in path.relative_to(root).parts):
            continue
        rel = path.relative_to(root).as_posix()
        raw = path.read_bytes()
        suffix = path.suffix.lower()
        if suffix in BINARY_SUFFIXES or suffix not in TEXT_SUFFIXES:
            payload = {"content": base64.b64encode(raw).decode("ascii"), "encoding": "base64"}
            kind = "base64"
        else:
            try:
                payload = {"content": raw.decode("utf-8"), "encoding": "utf-8"}
                kind = "utf-8"
            except UnicodeDecodeError:
                payload = {"content": base64.b64encode(raw).decode("ascii"), "encoding": "base64"}
                kind = "base64"
        files.append((rel, len(raw), kind, payload))
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="local directory whose files are published")
    ap.add_argument("--repo", default="shawn2016/shawn2016.github.io")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--message", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = Path(args.dir).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")

    files = collect(root)
    if not files:
        raise SystemExit("no files to publish")
    print(f"repo={args.repo} branch={args.branch} files={len(files)}")
    for rel, size, kind, _ in files:
        print(f"  {size:>9,} B  {kind:<6}  {rel}")
    if args.dry_run:
        print("\n[dry-run] nothing submitted")
        return

    base = f"/repos/{args.repo}/git"
    head = gh("GET", f"{base}/ref/heads/{args.branch}", jq=".object.sha")
    if not isinstance(head, str) or len(head) != 40:
        raise SystemExit(f"unexpected head sha: {head!r}")
    commit = gh("GET", f"{base}/commits/{head}")
    base_tree = commit["tree"]["sha"]
    print(f"\nhead={head} base_tree={base_tree}")

    tree_entries = []
    for rel, _, _, payload in files:
        blob = gh("POST", f"{base}/blobs", payload)
        tree_entries.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print(f"  blob {blob['sha'][:8]}  {rel}")

    tree = gh("POST", f"{base}/trees", {"base_tree": base_tree, "tree": tree_entries})
    new_commit = gh("POST", f"{base}/commits", {"message": args.message, "tree": tree["sha"], "parents": [head]})
    gh("PATCH", f"{base}/refs/heads/{args.branch}", {"sha": new_commit["sha"]})
    print(f"\ncommit {new_commit['sha']}\nhttps://github.com/{args.repo}/commit/{new_commit['sha']}")

    # REST commits endpoint (not /git/commits) is the one that returns a file list.
    check = gh("GET", f"/repos/{args.repo}/commits/{new_commit['sha']}")
    names = [f["filename"] for f in check.get("files", [])]
    print(f"committed files: {len(names)}")
    for name in names:
        print(f"  {name}")


if __name__ == "__main__":
    main()
