#!/usr/bin/env python3
"""anote index —— 分层索引（薄适配器；逻辑在 services/index.py）。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.index import gen_index, walk_notes  # noqa: E402


def main() -> int:
    dry = "--dry" in sys.argv[1:]
    src = Config.load().data_dir / "src"
    if not src.is_dir():
        print(f"未找到 {src}")
        return 1
    tree = walk_notes(str(src))
    for rel in sorted(tree, key=lambda r: r.count(os.sep)):
        if rel == "." or (tree[rel]["notes"] or tree[rel]["subdirs"]):
            out = os.path.join(src, rel, "00-index.tex")
            content = gen_index(rel, tree, str(src))
            if dry:
                print(f"[dry] {out} ({len(content)} bytes)")
            else:
                open(out, "w", encoding="utf-8").write(content)
                print(f"✓ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
