#!/usr/bin/env python3
"""anote md —— 终端 Markdown 渲染（薄适配器；逻辑在 services/mdview.py）。

接口声明（契约）:
    输入: <文件.md|.tex> [--watch]
    输出: ANSI 彩色文本到 stdout；退出码 0/1
    副作用: 无
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.mdview import render  # noqa: E402

CLEAR = "\x1b[2J\x1b[H"


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("用法: anote md <文件.md|.tex> [--watch]")
        return 1
    data = Config.load().data_dir
    inp = Path(os.path.expanduser(args[0]))
    if not inp.exists() and (data / args[0]).exists():
        inp = data / args[0]
    if not inp.exists():
        print(f"✗ 不存在: {inp}")
        return 1
    watch = "--watch" in args

    def show():
        text = inp.read_text(encoding="utf-8", errors="ignore")
        sys.stdout.write(CLEAR + render(text) + "\n")
        sys.stdout.flush()

    show()
    if not watch:
        return 0
    mtime = inp.stat().st_mtime
    try:
        while True:
            time.sleep(0.8)
            m = inp.stat().st_mtime
            if m != mtime:
                mtime = m
                show()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
