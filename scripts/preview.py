#!/usr/bin/env python3
"""anote preview —— Markdown/TEX 浏览器预览（薄适配器；逻辑在 services/preview.py）。

接口声明（契约）:
    输入: <文件> [--watch] [--out 路径]
    输出: stdout=预览地址；退出码 0/1
    副作用: 生成 HTML（默认 <数据根>/.anote/previews/）并打开浏览器
"""
import os
import subprocess
import sys
import threading
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.preview import render, watch_loop  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("用法: anote preview <文件.md|.tex> [--watch]")
        return 1
    data = Config.load().data_dir
    inp = Path(os.path.expanduser(args[0]))
    if not inp.exists() and (data / args[0]).exists():
        inp = data / args[0]
    if not inp.exists():
        print(f"✗ 不存在: {inp}")
        return 1

    watch = "--watch" in args
    out = data / ".anote" / "previews" / f"{inp.stem}.html"
    if "--out" in args:
        i = args.index("--out")
        if i + 1 < len(args):
            out = Path(os.path.expanduser(args[i + 1]))
    try:
        render(inp, out)
    except RuntimeError as e:
        print(f"✗ {e}")
        return 1

    if watch:
        threading.Thread(target=watch_loop, args=(inp, out), daemon=True).start()
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


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
