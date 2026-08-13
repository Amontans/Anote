#!/usr/bin/env python3
"""anote convert —— 万能文档转换（pandoc 包装，40+ 格式双向互通）。

接口声明（契约）:
    输入: <输入文件> [--out 输出文件] [--to 格式] [--from 格式] [--pdf-engine xelatex]
    输出: stdout=转换报告；退出码 0/1
    副作用: 写输出文件
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402

EXT_TO_FORMAT = {
    ".md": "gfm", ".markdown": "gfm", ".tex": "latex", ".docx": "docx",
    ".pptx": "pptx", ".odt": "odt", ".epub": "epub", ".ipynb": "ipynb",
    ".org": "org", ".rst": "rst", ".html": "html", ".htm": "html",
    ".csv": "csv", ".txt": "markdown", ".pdf": "pdf",
}


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print("用法: anote convert <输入文件> [--out 输出] [--to 格式] [--from 格式] [--pdf-engine xelatex]")
        return 1
    inp = Path(os.path.expanduser(args[0]))
    if not inp.exists():
        print(f"✗ 不存在: {inp}")
        return 1
    def av(flag):
        return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else None

    out = Path(os.path.expanduser(av("--out") or inp.with_suffix(".md")))
    to_fmt = av("--to") or EXT_TO_FORMAT.get(out.suffix.lower(), "gfm")
    from_fmt = av("--from") or EXT_TO_FORMAT.get(inp.suffix.lower(), "gfm")
    engine = av("--pdf-engine") or ("xelatex" if to_fmt == "pdf" else None)

    cmd = ["pandoc", str(inp), "-f", from_fmt, "-t", to_fmt, "-o", str(out)]
    if engine:
        cmd += ["--pdf-engine", engine]
    # 中文支持
    if to_fmt in ("pdf", "latex", "beamer"):
        cmd += ["-V", "CJKmainfont=Noto Serif CJK SC"] if engine == "xelatex" else []
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"✗ 转换失败: {r.stderr.strip()[:300]}")
        return 1
    print(f"✓ 已转换: {inp} → {out}（{from_fmt} → {to_fmt}）")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
