#!/usr/bin/env python3
"""anote index-pdf —— 批量提取 pdfs/ 文本（使 PDF 可被检索）。"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.ebooks import extract_pdf_text  # noqa: E402


def main() -> int:
    data = Path(Config.load().data_dir)
    pdf_dir = data / "pdfs"
    if not pdf_dir.is_dir():
        print("pdfs/ 不存在")
        return 0
    n = 0
    for p in sorted(pdf_dir.glob("*.pdf")):
        txt = p.with_suffix(".txt")
        if txt.exists():
            continue
        extract_pdf_text(p, txt)
        print(f"  ✓ {p.name} → {txt.name}")
        n += 1
    print(f"\n提取 {n} 个 PDF 文本（txt 可被 anote ask 检索；pdfs/*.txt 不入 git）")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
