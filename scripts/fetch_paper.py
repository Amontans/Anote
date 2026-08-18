#!/usr/bin/env python3
"""anote fetch_paper —— 论文下载/提取/精读笔记（薄适配器；逻辑在 services/papers.py）。

接口声明（契约）:
    输入: --arxivid <id> | --doi <doi> | --url <url> [--dir 目录] [--no-extract]
          [--tex-note [目录]]
    输出: stdout=下载/提取/笔记路径；退出码 0/1
    副作用: 下载 PDF 到 <数据根>/pdfs（默认），提取 .txt，可选生成 TEX 精读笔记
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import literature as lit  # noqa: E402
from anote.services import papers  # noqa: E402


def _flag_value(args, flag, default=None):
    if flag not in args:
        return default
    i = args.index(flag)
    if i + 1 < len(args) and not args[i + 1].startswith("--"):
        return args[i + 1]
    return default


def _metadata(arxivid=None, doi=None, url=None) -> dict:
    """尽力取元数据（失败时返回空字典，不阻断下载）。"""
    try:
        if arxivid:
            rows = lit.arxiv_search(f"id:{arxivid}", 1)
            if rows:
                return rows[0]
        elif doi:
            rows = lit.crossref_doi(doi)
            if rows:
                return rows[0]
    except Exception:  # noqa: BLE001
        pass
    return {"url": url or ""}


def main() -> int:
    args = sys.argv[1:]
    data = Config.load().data_dir
    arxivid = _flag_value(args, "--arxivid")
    doi = _flag_value(args, "--doi")
    url = _flag_value(args, "--url")
    out_dir = _flag_value(args, "--dir", str(data / "pdfs"))
    no_extract = "--no-extract" in args
    tex_note = None
    if "--tex-note" in args:
        tex_note = _flag_value(args, "--tex-note", str(data / "src" / "papers"))

    if not (arxivid or doi or url):
        print("需要 --arxivid / --doi / --url 之一")
        return 1

    meta = _metadata(arxivid=arxivid, doi=doi, url=url)
    meta["arxiv_id"] = arxivid or meta.get("arxiv_id", "")
    meta["doi"] = doi or meta.get("doi", "")

    try:
        if arxivid:
            pdf = papers.arxiv_pdf(arxivid, out_dir)
        elif doi:
            pdf = papers.doi_pdf(doi, out_dir)
        else:
            name = os.path.basename(url.split("?")[0]) or "paper.pdf"
            pdf = papers.download(url, out_dir, name)
    except SystemExit:
        raise
    if not no_extract:
        papers.extract(pdf)
    if tex_note:
        meta["url"] = meta.get("url") or (f"https://arxiv.org/abs/{arxivid}" if arxivid else url or "")
        note = papers.gen_tex_note(meta, tex_note)
        print(f"TEX 精读笔记: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
