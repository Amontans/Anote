#!/usr/bin/env python3
"""Download a paper PDF (arXiv ID / DOI / URL) and extract text via pdftotext."""
import argparse
import os
import re
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote import cli as _cli  # noqa: E402

def arxiv_pdf(arxivid, out_dir):
    url = f"https://arxiv.org/pdf/{arxivid}"
    return download(url, out_dir, f"{arxivid}.pdf", expected_host="arxiv.org")


def doi_pdf(doi, out_dir):
    # resolve DOI -> publisher landing page (follow redirects)
    url = f"https://doi.org/{doi}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 paper-reading-skill"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            final = r.geturl()
    except Exception as e:  # noqa: BLE001
        print(f"DOI 解析失败: {e}\n请手动提供 PDF 直链 (--url)。")
        sys.exit(1)
    print(f"DOI 重定向至: {final}")
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", doi) + ".pdf"
    if final.endswith(".pdf"):
        return download(final, out_dir, name)
    print(f"落地页 {final} 不是 PDF 直链，可能需要代理或手动下载。")
    sys.exit(1)


def download(url, out_dir, filename, expected_host=None):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 paper-reading-skill"})
    print(f"下载 {url}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
            if expected_host and r.geturl() and expected_host not in r.geturl():
                print(f"警告: 实际落到 {r.geturl()}，可能是反爬/重定向页。")
            content_type = r.headers.get("Content-Type", "")
            if "pdf" not in content_type and not data[:5].startswith(b"%PDF"):
                print("警告: 响应不是 PDF（可能被拦截）。尝试 --url 直链。")
    except Exception as e:  # noqa: BLE001
        print(f"下载失败: {e}")
        sys.exit(1)
    with open(path, "wb") as f:
        f.write(data)
    print(f"已保存 {path} ({len(data)/1024:.0f} KB)")
    return path


def extract(pdf, out_txt=None):
    if not out_txt:
        out_txt = os.path.splitext(pdf)[0] + ".txt"
    r = subprocess.run(["pdftotext", "-layout", pdf, out_txt], capture_output=True)
    if r.returncode != 0:
        print(f"pdftotext 失败: {r.stderr.decode()}")
        sys.exit(1)
    print(f"文本已提取 {out_txt}")
    return out_txt


def gen_tex_note(meta, out_dir="~/Projects/notes/src/papers"):
    """按模板生成 TEX 精读笔记（AI 之后补内容）"""
    import datetime
    tpl = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "templates", "reading-note.tex")
    with open(tpl, encoding="utf-8") as f:
        content = f.read()
    title = meta.get("title", os.path.basename(meta.get("url", "note")))
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "_", title)[:40]
    authors = meta.get("authors", []) or []
    author = (authors[0] if authors else "")
    today = datetime.date.today().isoformat()
    out_dir = os.path.expanduser(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{today}_{slug}.tex")
    meta_line = " | ".join(filter(None, [
        meta.get("arxiv_id") or "", meta.get("doi") or "",
        author, str(meta.get("year", ""))]))
    content = content.replace("%%TITLE%%", title).replace("%%META%%", meta_line)
    if not os.path.exists(out):
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)
    return out


def main():
    ap = argparse.ArgumentParser(description="Download & extract paper PDF")
    ap.add_argument("--arxivid")
    ap.add_argument("--doi")
    ap.add_argument("--url")
    ap.add_argument("--dir", default="~/Projects/notes/pdfs")
    ap.add_argument("--no-extract", action="store_true")
    ap.add_argument("--tex-note", nargs="?", const="~/Projects/notes/src/papers",
                    help="同时生成 TEX 精读笔记（默认目录 ~/Projects/notes/src/papers）")
    a = ap.parse_args()

    out_dir = os.path.expanduser(a.dir)
    pdf = None
    if a.arxivid:
        pdf = arxiv_pdf(a.arxivid, out_dir)
    elif a.doi:
        pdf = doi_pdf(a.doi, out_dir)
    elif a.url:
        name = os.path.basename(a.url.split("?")[0]) or "paper.pdf"
        pdf = download(a.url, out_dir, name)
    else:
        ap.error("需要 --arxivid / --doi / --url 之一")
    if not a.no_extract:
        extract(pdf)
    if a.tex_note:
        meta = {"title": os.path.basename(a.arxivid or a.doi or pdf)[:60],
                "arxiv_id": a.arxivid, "doi": a.doi,
                "url": a.url or f"https://arxiv.org/abs/{a.arxivid}" if a.arxivid else ""}
        note = gen_tex_note(meta, a.tex_note)
        print(f"TEX 精读笔记: {note}")


if __name__ == "__main__":
    sys.exit(_cli.run(main))
