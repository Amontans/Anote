"""只读 Web 外壳服务：浏览数据根 + 全文搜索。

安全：只绑定本机；禁止访问 .git/.venv/.semantic/.anote。
"""
from __future__ import annotations

import html
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

FORBIDDEN_FIRST = {".git", ".venv", ".semantic", ".anote"}


def create_handler(data_dir: Path, token: str | None = None):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(data_dir), **kw)

        def _check_token(self, qs) -> bool:
            if token is None:
                return True
            return qs.get("t", [""])[0] == token

        def _forbidden(self, path: str) -> bool:
            first = path.lstrip("/").split("/", 1)[0]
            return first in FORBIDDEN_FIRST

        def do_GET(self):
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            if not self._check_token(qs):
                self.send_error(403, "Forbidden")
                return
            if self._forbidden(parsed.path):
                self.send_error(404, "Not Found")
                return
            if parsed.path == "/":
                self._index()
            elif parsed.path == "/search":
                self._search(qs.get("q", [""])[0])
            else:
                super().do_GET()

        def _index(self):
            items = []
            for d in sorted(p for p in data_dir.iterdir()
                            if p.is_dir() and p.name not in (".venv", ".semantic", ".git", ".anote")):
                items.append(f'<li><a href="/{html.escape(d.name)}/">{html.escape(d.name)}/</a></li>')
            self._html("Anote 只读浏览",
                       f"<h1>Anote 知识库</h1>"
                       f"<form action='/search'><input name='q' placeholder='全文搜索'><button>搜索</button></form>"
                       f"<ul>{''.join(items)}</ul>")

        def _search(self, q):
            q = q.strip()
            if not q:
                self._html("搜索", "<p>输入关键词</p>")
                return
            try:
                r = subprocess.run(["rg", "-n", "-i", q, str(data_dir), "-g", "*.tex", "-g", "*.md",
                                    "-g", "!00-index.tex", "-g", "!README.md"],
                                   capture_output=True, text=True, timeout=20)
                lines = r.stdout.splitlines()[:100]
            except FileNotFoundError:
                lines = ["（未安装 rg）"]
            body = [f"<h1>搜索: {html.escape(q)}</h1><p>{len(lines)} 条</p><ul>"]
            for ln in lines:
                p, _, rest = ln.partition(":")
                rel = p[len(str(data_dir)) + 1:] if p.startswith(str(data_dir)) else p
                body.append(f"<li><a href='/{html.escape(rel)}'>{html.escape(rel)}</a>: {html.escape(rest[:100])}</li>")
            body.append("</ul>")
            self._html("搜索", "".join(body))

        def _html(self, title, body):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                f"<!doctype html><meta charset=utf-8><title>{html.escape(title)}</title>"
                f"<style>body{{font-family:sans-serif;max-width:900px;margin:2em auto}}a{{color:#0366d6}}</style>"
                f"{body}".encode("utf-8"))

        def log_message(self, *a):
            pass

    return Handler


def serve(data_dir: Path, port: int = 8765, token: str | None = None) -> None:
    handler = create_handler(data_dir, token)
    srv = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Anote 只读外壳: http://127.0.0.1:{port}/  （仅本机，Ctrl+C 停止）")
    if token:
        print(f"  口令: ?t={token}")
    srv.serve_forever()
