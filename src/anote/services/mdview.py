"""终端 Markdown 渲染服务（纯 stdlib，零依赖）。"""
from __future__ import annotations

import re

B = "\033[1m"; I = "\033[3m"; DIM = "\033[2m"
BLUE = "\033[34m"; GREEN = "\033[32m"; YELLOW = "\033[33m"; GREY = "\033[90m"
R = "\033[0m"

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
    """Markdown/兼容 TEX 历史文件 → ANSI 彩色文本。"""
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
            out.append("  " + YELLOW + ln.strip().split(".", 1)[0] + "." + R +
                       inline(ln.strip().split(".", 1)[1]))
        elif ln.strip().startswith(">"):
            out.append(f"{GREY}  │ {inline(ln.strip()[1:].strip())}{R}")
        elif re.match(r"^\s*\|.*\|\s*$", ln) and "-" in ln:
            out.append(f"{GREY}{ln.strip()}{R}")
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
