#!/usr/bin/env python3
"""anote wiki —— 知识编译层（薄适配器；逻辑在 services/wiki.py）。"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import NotesService  # noqa: E402
from anote.services.wiki import compile_theme, group_notes  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    dry = "--dry" in args
    force = "--force" in args
    data = Config.load().data_dir
    groups = group_notes(NotesService(data).scan())
    print(f"知识编译计划（{len(groups)} 个主题）")
    for (disc, branch), ns in sorted(groups.items()):
        print(f"  • {disc or '?'}/{branch or '?'}: {len(ns)} 篇")
    if dry:
        print("\n（--dry：未生成）")
        return 0
    for (disc, branch), ns in sorted(groups.items()):
        out, err = compile_theme(disc, branch, ns, Path(data), force)
        if err:
            print(f"  ✗ {disc}/{branch}: {err.stderr}")
        elif out.exists():
            print(f"  ✓ 已生成 {out.relative_to(data)}")
        else:
            print(f"  ⏭ {out.name} 已存在（--force 重建）")
    print("\n完成。请人工确认主题页内容。")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
