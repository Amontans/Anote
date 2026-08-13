#!/usr/bin/env python3
"""anote docs annotations —— Zotero/阅读器标注导入（M4）。

接口声明（契约）:
    输入: <标注文件(.md/.txt)> [--to 笔记路径]
    输出: stdout=导入报告；退出码 0/1
    副作用: 追加到笔记 或 写 docs/annotations/<名>.md
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("用法: anote docs annotations <标注文件> [--to 笔记路径]")
        return 1
    src_f = Path(os.path.expanduser(args[0]))
    if not src_f.exists():
        print(f"✗ 不存在: {src_f}")
        return 1
    text = src_f.read_text(encoding="utf-8", errors="ignore")
    data = Path(Config.load().data_dir)
    to = None
    if "--to" in args:
        to = data / args[args.index("--to") + 1]
    if to is None:
        d = data / "docs" / "annotations"
        d.mkdir(parents=True, exist_ok=True)
        to = d / (src_f.stem + ".md")
    header = f"\n\n## 标注导入（{src_f.name}）\n" + text.strip()
    if to.exists():
        to.write_text(to.read_text(encoding="utf-8") + header, encoding="utf-8")
    else:
        to.write_text("# 标注\n" + header, encoding="utf-8")
    print(f"✓ 标注已导入: {to}")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
