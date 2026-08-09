#!/usr/bin/env python3
"""反链视图（v1.1）：<概念> 被哪些笔记/记忆引用——rg 计数 + META 标签匹配。

用法:
  backlinks.py "<概念>"
  backlinks.py --json "<概念>"
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("term", help="概念/词")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    data = Path(Config.load().data_dir)
    term = a.term

    # rg 计数（每文件出现行数）
    cmd = ["rg", "-c", "-i", term, str(data),
           "-g", "*.tex", "-g", "*.md",
           "-g", "!00-index.tex", "-g", "!README.md", "-g", "!queue.md"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        print("未找到 rg（安装 ripgrep）")
        sys.exit(1)

    refs = []
    for line in proc.stdout.splitlines():
        p, _, count = line.rpartition(":")
        if not p or not count.isdigit():
            continue
        refs.append({"file": p.replace(str(data) + "/", ""), "count": int(count)})
    refs.sort(key=lambda r: -r["count"])

    # META 标签命中
    tags = []
    for root, _, fs in os.walk(data / "src"):
        for f in fs:
            if not f.endswith((".tex", ".md")) or f in ("00-index.tex",):
                continue
            fp = Path(root) / f
            try:
                head = fp.read_text(encoding="utf-8")[:400]
            except OSError:
                continue
            if term in head:
                tags.append(str(fp.relative_to(data)))

    if a.json:
        print(json.dumps({"refs": refs, "meta_hits": tags}, ensure_ascii=False, indent=2))
        return

    print(f"反链：『{term}』\n")
    if refs:
        print("被引用（按次数）:")
        for r in refs[:20]:
            print(f"  {r['count']:3d}×  {r['file']}")
    else:
        print("（无全文引用）")
    if tags:
        print(f"\nMETA 标签命中 {len(tags)} 处:")
        for t in tags[:10]:
            print(f"  •  {t}")
    print(f"\n共 {len(refs)} 个文件引用 + {len(tags)} 处标签命中")


if __name__ == "__main__":
    main()
