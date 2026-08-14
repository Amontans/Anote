#!/usr/bin/env python3
"""anote md —— 终端 Markdown 渲染（极简、零依赖、实时）。

用法:
  anote md 文件.md                # 渲染一次
  anote md 文件.md --watch        # 实时：文件变化自动重渲染（Vim 分屏用）

Vim 集成: :vert term anote md % --watch   （右侧分屏，保存即刷新）
接口声明（契约）:
    输入: <文件.md|.tex> [--watch]
    输出: ANSI 彩色文本到 stdout；退出码 0/1
    副作用: 无
"""
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

B = "\033[1m"; I = "\033[3m"; DIM = "\033[2m"
BLUE = "\033[34m"; GREEN = "\033[32m"; YELLOW = "\033[33m"; GREY = "\033[90m"
R = "\033[0m"
CLEAR = "\x1b[2J\x1b[H"

INLINE = [
    (re.compile(r"\*\*(.+?)\*\*"), f"{B}\\1{R}"),
    (re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)"), f"{I}\\1{R}"),
    (re.compile(r"`([^`]+)`"), f"{GREEN}\\1{R}"),
    (re.compile(r"\[([^\]]+)\]\([^)]+\)"), f"{BLUE}\\1{R}"),
]


def inline(s: str) -> str:
    for pat, repl in INLINE:
        s = pat.sub(repl, s)
    return s


def render(text: str) -> str:
    lines = text.splitlines()
    out, i, code = [], 0, False
    while i < len(lines):
        ln = lines[i]
        if not code and (ln.strip().startswith("%") or re.match(r"^\s*\\[a-zA-Z]", ln)):
            i += 1  # 跳过 LaTeX 注释/命令（兼容历史文件）
            continue
        if ln.strip().startswith("```"):
            code = not code
            out.append(f"{GREY}{'┌ ' + ln.strip()[3:][:30]}{R}" if code else f"{GREY}└{R}")
            i += 1
            continue
        if code:
            out.append(f"{GREY}{ln}{R}")
        elif ln.strip().startswith("#"):
            level = len(ln) - len(ln.lstrip("#"))
            out.append(f"{B}{BLUE}{ln.strip('# ')}{R}")
        elif ln.strip().startswith(("- ", "* ", "+ ")):
            out.append("  " + YELLOW + "• " + R + inline(ln.strip()[2:]))
        elif re.match(r"^\d+\. ", ln.strip()):
            out.append("  " + YELLOW + ln.strip().split(".", 1)[0] + "." + R + inline(ln.strip().split(".", 1)[1]))
        elif ln.strip().startswith(">"):
            out.append(f"{GREY}  │ {inline(ln.strip()[1:].strip())}{R}")
        elif re.match(r"^\s*\|.*\|\s*$", ln) and "-" in ln:
            out.append(f"{GREY}{ln.strip()}{R}")  # 表头分隔
        elif re.match(r"^\s*\|", ln):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            out.append("  " + " │ ".join(inline(c) for c in cells))
        elif re.match(r"^\s*[-=]{3,}\s*$", ln):
            out.append(f"{GREY}{'─' * 40}{R}")
        elif ln.strip():
            out.append(inline(ln))
        else:
            out.append("")
        i += 1
    return "\n".join(out)


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("用法: anote md <文件.md|.tex> [--watch]")
        return 1
    from anote.core import Config
    data = Path(Config.load().data_dir)
    inp = Path(os.path.expanduser(args[0]))
    if not inp.exists() and (data / args[0]).exists():
        inp = data / args[0]
    if not inp.exists():
        print(f"✗ 不存在: {inp}")
        return 1
    watch = "--watch" in args

    def show():
        try:
            text = inp.read_text(encoding="utf-8", errors="ignore")
            sys.stdout.write(CLEAR + render(text) + "\n")
            sys.stdout.flush()
        except Exception:  # noqa: BLE001
            pass

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
