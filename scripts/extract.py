#!/usr/bin/env python3
"""Extract text from a PDF via pdftotext (thin wrapper)."""
import argparse
import os
import subprocess
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote import cli as _cli  # noqa: E402

def main():
    ap = argparse.ArgumentParser(description="Extract text from PDF")
    ap.add_argument("pdf")
    ap.add_argument("--out")
    a = ap.parse_args()
    if not os.path.exists(a.pdf):
        sys.exit(f"文件不存在: {a.pdf}")
    out = a.out or os.path.splitext(a.pdf)[0] + ".txt"
    r = subprocess.run(["pdftotext", "-layout", a.pdf, out], capture_output=True)
    if r.returncode != 0:
        sys.exit(f"pdftotext 失败: {r.stderr.decode()}")
    words = sum(len(l.split()) for l in open(out, encoding="utf-8", errors="ignore"))
    print(f"{a.pdf} -> {out} (约 {words} 词)")

if __name__ == "__main__":
    sys.exit(_cli.run(main))
