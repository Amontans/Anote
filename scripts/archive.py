#!/usr/bin/env python3
"""anote archive —— 年度归档（v1.8）：把 META 日期早于某年的笔记移入 src/_archive/<年>/。

归档目录以下划线开头 → NotesService 自动跳过（不影响检索/统计/索引）。
接口声明（契约）:
    输入: <年份> [--dry]
    输出: stdout=移动清单；退出码 0/1
    副作用: 移动文件（git 可回滚）
"""
import datetime
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import NotesService  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    if not args or not args[0].isdigit():
        print("用法: anote archive <年份> [--dry]")
        return 1
    year = int(args[0])
    dry = "--dry" in args
    data = Path(Config.load().data_dir)
    notes = NotesService(data).scan()
    moved = 0
    for n in notes:
        d = n.meta.get("日期", "")
        try:
            ny = int(d[:4])
        except (ValueError, TypeError):
            continue
        if ny >= year:
            continue
        src = Path(data) / n.rel
        dst_dir = data / "src" / "_archive" / str(year) / n.rel[len("src/"):].rsplit("/", 1)[0] if "/" in n.rel[len("src/"):] else data / "src" / "_archive" / str(year)
        dst = dst_dir / src.name
        if dry:
            print(f"  [dry] {n.rel} → _archive/{year}/")
            moved += 1
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        print(f"  ✓ {n.rel} → _archive/{year}/")
        moved += 1
    print(f"\n归档 {moved} 篇到 src/_archive/{year}/（归档目录自动排除在检索/统计外）")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
