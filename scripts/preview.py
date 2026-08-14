#!/usr/bin/env python3
"""anote preview —— Markdown/TEX 预览（pandoc → 美化 HTML → 浏览器；可选 --watch 自动刷新）。

接口声明（契约）:
    输入: <文件> [--watch] [--out 路径]
    输出: stdout=预览地址；退出码 0/1
    副作用: 生成临时 HTML；--watch 后台循环重渲染
"""
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

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
    # 转 HTML（md→gfm；tex→latex）
    fmt = "latex" if inp.suffix.lower() in (".tex",) else "gfm"
    body = subprocess.run(["pandoc", str(inp), "-f", fmt, "-t", "html", "--standalone",
                           "--metadata", f"title={inp.stem}",
                           "--metadata", "lang=zh-CN"],
                          capture_output=True, text=True).stdout
    # 注入 CSS + MathJax（CDN，离线时公式退化为文本）
    html = body.replace("</head>",
                        f"<style>{CSS}</style>"
                        '<script>window.MathJax={tex:{inlineMath:[["$","$"],["\\\\(","\\\\)"]]}};</script>'
                        '<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>'
                        "</head>")
    out.write_text(html, encoding="utf-8")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("用法: anote preview <文件.md|.tex> [--watch]")
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
    out = Path("/tmp") / f"anote-preview-{inp.stem}.html"
    if "--out" in args:
        out = Path(os.path.expanduser(args[args.index("--out") + 1]))

    render(inp, out)

    if watch:
        # 后台循环重渲染 + 页面 meta 自动刷新（live 预览）
        t = threading.Thread(target=_watch_loop, args=(inp, out), daemon=True)
        t.start()
        # 注入自动刷新
        html = out.read_text(encoding="utf-8")
        html = html.replace("</head>", '<meta http-equiv="refresh" content="2"></head>', 1)
        out.write_text(html, encoding="utf-8")
        print(f"⏳ 实时预览（保存后 2 秒内刷新）: {out}")
    else:
        print(f"✓ 预览已生成: {out}")

    opener = os.environ.get("BROWSER") or "xdg-open"
    subprocess.Popen([opener, str(out)], start_new_session=True)
    print("  浏览器中按 Ctrl+C 可关闭（若在终端前台）")
    return 0


def _watch_loop(inp: Path, out: Path) -> None:
    mtime = 0
    while True:
        try:
            m = inp.stat().st_mtime
            if m != mtime:
                mtime = m
                render(inp, out)
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1.5)


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
