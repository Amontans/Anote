#!/usr/bin/env python3
"""anote fetch_paper —— 论文下载/提取/精读笔记（薄适配器；逻辑在 services/papers.py）。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.services import papers  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    arxivid = None
    if "--arxivid" in args:
        arxivid = args[args.index("--arxivid") + 1]
    doi = None
    if "--doi" in args:
        doi = args[args.index("--doi") + 1]
    url = None
    if "--url" in args:
        url = args[args.index("--url") + 1]
    out_dir = "~/papers/pdf"
    if "--dir" in args:
        out_dir = args[args.index("--dir") + 1]
    no_extract = "--no-extract" in args
    tex_note = None
    if "--tex-note" in args:
        i = args.index("--tex-note")
        tex_note = args[i + 1] if i + 1 < len(args) and not args[i + 1].startswith("--") else "~/Documents/Anote/src/papers"

    if arxivid:
        pdf = papers.arxiv_pdf(arxivid, out_dir)
    elif doi:
        pdf = papers.doi_pdf(doi, out_dir)
    elif url:
        name = os.path.basename(url.split("?")[0]) or "paper.pdf"
        pdf = papers.download(url, out_dir, name)
    else:
        print("需要 --arxivid / --doi / --url 之一")
        return 1
    if not no_extract:
        papers.extract(pdf)
    if tex_note:
        meta = {"arxiv_id": arxivid, "doi": doi,
                "url": url or (f"https://arxiv.org/abs/{arxivid}" if arxivid else "")}
        note = papers.gen_tex_note(meta, tex_note)
        print(f"TEX 精读笔记: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
