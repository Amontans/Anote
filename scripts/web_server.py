#!/usr/bin/env python3
"""anote web —— 局域网只读浏览外壳（v1.5）：浏览 src/memory/wiki + 全文搜索。

安全: 仅监听 127.0.0.1；只读；可选 --token 口令（URL 带 ?t= 或头）。
接口声明（契约）:
    输入: argv: [--port N] [--token xxx]
    输出: HTTP；退出码 0/1
    副作用: 无（只读）
"""
import argparse
import html
import os
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402

DATA = Path(Config.load().data_dir)
TOKEN = None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DATA), **kw)

    def _check_token(self, qs) -> bool:
        if TOKEN is None:
            return True
        return qs.get("t", [""])[0] == TOKEN

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if not self._check_token(qs):
            self.send_error(403, "口令错误")
            return
        if parsed.path == "/":
            self._index()
        elif parsed.path == "/search":
            self._search(qs.get("q", [""])[0])
        else:
            super().do_GET()

    def _index(self):
        items = []
        for d in sorted(p for p in DATA.iterdir() if p.is_dir() and p.name not in (".venv", ".semantic", ".git")):
            items.append(f'<li><a href="/{html.escape(d.name)}/">{html.escape(d.name)}/</a></li>')
        self._html("Anote 只读浏览", f"<h1>Anote 知识库</h1><form action='/search'><input name='q' placeholder='全文搜索'><button>搜索</button></form><ul>{''.join(items)}</ul>")

    def _search(self, q):
        q = q.strip()
        if not q:
            self._html("搜索", "<p>输入关键词</p>")
            return
        try:
            r = subprocess.run(["rg", "-n", "-i", q, str(DATA), "-g", "*.tex", "-g", "*.md",
                                "-g", "!00-index.tex", "-g", "!README.md"],
                               capture_output=True, text=True, timeout=20)
            lines = r.stdout.splitlines()[:100]
        except FileNotFoundError:
            lines = ["（未安装 rg）"]
        body = [f"<h1>搜索: {html.escape(q)}</h1><p>{len(lines)} 条</p><ul>"]
        for ln in lines:
            p, _, rest = ln.partition(":")
            body.append(f"<li><a href='/{html.escape(p[len(str(DATA))+1:] if p.startswith(str(DATA)) else p)}'>{html.escape(p[len(str(DATA))+1:] if p.startswith(str(DATA)) else p)}</a>: {html.escape(rest[:100])}</li>")
        body.append("</ul>")
        self._html("搜索", "".join(body))

    def _html(self, title, body):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(f"<!doctype html><meta charset=utf-8><title>{html.escape(title)}</title>"
                         f"<style>body{{font-family:sans-serif;max-width:900px;margin:2em auto}}a{{color:#0366d6}}</style>"
                         f"{body}".encode("utf-8"))

    def log_message(self, *a):
        pass


def main() -> int:
    global TOKEN
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--token", default=None)
    a = ap.parse_args()
    TOKEN = a.token
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"Anote 只读外壳: http://127.0.0.1:{a.port}/  （仅本机，Ctrl+C 停止）")
    if TOKEN:
        print(f"  口令: ?t={TOKEN}")
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
