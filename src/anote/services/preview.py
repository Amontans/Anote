"""Markdown/TEX 预览服务：pandoc → HTML（GitHub 风格 + MathJax）。"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

CSS = """
body{max-width:820px;margin:2em auto;padding:0 1em;font-family:-apple-system,'Noto Sans CJK SC',sans-serif;
     line-height:1.7;color:#24292f;background:#fff}
h1,h2,h3{border-bottom:1px solid #eaecef;padding-bottom:.3em}
code{background:#f6f8fa;padding:.2em .4em;border-radius:4px;font-size:.9em}
pre code{display:block;padding:1em;overflow-x:auto}
blockquote{color:#57606a;border-left:4px solid #d0d7de;margin:0;padding:0 1em}
table{border-collapse:collapse}th,td{border:1px solid #d0d7de;padding:.4em .8em}
a{color:#0969da}
"""


def render(inp: Path, out: Path) -> None:
    """转 HTML：md→gfm，tex→latex；注入 CSS 与 MathJax。"""
    fmt = "latex" if inp.suffix.lower() == ".tex" else "gfm"
    proc = subprocess.run(["pandoc", str(inp), "-f", fmt, "-t", "html", "--standalone",
                           "--metadata", f"title={inp.stem}",
                           "--metadata", "lang=zh-CN"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:300] or "pandoc 转换失败")
    html = proc.stdout.replace(
        "</head>",
        f"<style>{CSS}</style>"
        '<script>window.MathJax={tex:{inlineMath:[["$","$"],["\\\\(","\\\\)"]]}};</script>'
        '<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>'
        "</head>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def watch_loop(inp: Path, out: Path, interval: float = 1.5) -> None:
    """后台循环重渲染；异常静默跳过，保存后自动刷新。"""
    mtime = 0.0
    while True:
        try:
            m = inp.stat().st_mtime
            if m != mtime:
                mtime = m
                render(inp, out)
        except Exception:  # noqa: BLE001
            pass
        time.sleep(interval)
