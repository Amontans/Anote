"""电子书/文档领域服务：epub 文本提取、PDF 文本提取、阅读器选择。"""
from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from html.parser import HTMLParser
from pathlib import Path


class _TextExtract(HTMLParser):
    """剥离 HTML → 纯文本。"""

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data):
        self.parts.append(data)


def extract_epub(path: Path) -> str:
    """epub（zip+HTML）→ 纯文本。"""
    chunks = []
    with zipfile.ZipFile(path) as z:
        htmls = sorted(n for n in z.namelist()
                       if n.lower().endswith((".html", ".xhtml", ".htm")))
        for name in htmls:
            p = _TextExtract()
            p.feed(z.read(name).decode("utf-8", errors="ignore"))
            text = " ".join(x.strip() for x in p.parts if x.strip())
            if text:
                chunks.append(text)
    return "\n\n".join(chunks)


def extract_pdf_text(pdf: Path, out_txt: Path | None = None) -> str:
    """PDF → 文本（pdftotext），可指定输出。"""
    out = out_txt or pdf.with_suffix(".txt")
    subprocess.run(["pdftotext", "-layout", str(pdf), str(out)], check=True)
    return out.read_text(encoding="utf-8", errors="ignore")


def pick_reader(path: Path, reader: str = "") -> str:
    """按文件类型与可用性选阅读器/编辑器命令。"""
    ext = path.suffix.lower()
    if reader and shutil.which(reader):
        return reader
    if ext == ".pdf":
        for r in ("zathura", "okular", "evince"):
            if shutil.which(r):
                return r
    if ext == ".epub":
        for r in ("foliate", "calibre", "ebook-viewer"):
            if shutil.which(r):
                return r
    if ext in (".mobi", ".azw3"):
        for r in ("ebook-viewer", "calibre", "foliate"):
            if shutil.which(r):
                return r
    for r in ("code", "vim", "nvim"):
        if shutil.which(r):
            return r
    return "xdg-open"
