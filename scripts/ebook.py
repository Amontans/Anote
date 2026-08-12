#!/usr/bin/env python3
"""anote ebook —— 电子书管理：list / extract（v1.9.1）。"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.ebooks import extract_epub, extract_pdf_text  # noqa: E402

EXTS = (".pdf", ".epub", ".mobi", ".azw3", ".txt")


def main() -> int:
    args = sys.argv[1:]
    data = Path(Config.load().data_dir)
    if not args or args[0] == "list":
        print("电子书/文档目录:")
        for d in ("pdfs", "ebooks"):
            dd = data / d
            if dd.is_dir():
                for f in sorted(p for p in dd.iterdir() if p.suffix.lower() in EXTS):
                    print(f"  • {d}/{f.name} ({f.stat().st_size/1024:.0f} KB)")
        return 0
    if args[0] == "extract" and len(args) > 1:
        p = data / args[1]
        if not p.exists():
            print(f"✗ 不存在: {p}")
            return 1
        if p.suffix.lower() == ".epub":
            out = p.with_suffix(".txt")
            out.write_text(extract_epub(p), encoding="utf-8")
            print(f"✓ epub → {out}（{len(out.read_text(encoding='utf-8'))} 字符，可被 anote ask 检索）")
            return 0
        if p.suffix.lower() == ".pdf":
            out = p.with_suffix(".txt")
            extract_pdf_text(p, out)
            print(f"✓ pdf → {out}")
            return 0
        print("✗ 支持 epub/pdf 提取；mobi 需 calibre（sudo pacman -S calibre 后: ebook-convert）")
        return 1
    print("用法: anote ebook [list | extract <路径>]")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
