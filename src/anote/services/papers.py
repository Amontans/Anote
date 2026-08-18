from __future__ import annotations

"""论文获取领域服务：下载 PDF / 提取文本 / 生成精读笔记（fetch_paper 薄适配器）。"""

import datetime
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

from ..core import Config, PROJECT_ROOT


def arxiv_pdf(arxivid, out_dir):
    url = f"https://arxiv.org/pdf/{arxivid}"
    return download(url, out_dir, f"{arxivid}.pdf", expected_host="arxiv.org")


def doi_pdf(doi, out_dir):
    """解析 DOI → 落地页；仅当落地页为 PDF 直链时可下载，否则给出提示。"""
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
    out_dir = os.path.expanduser(out_dir)
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


def gen_tex_note(meta, out_dir=None):
    """按模板生成 TEX 精读笔记（含 META 块，AI 之后补内容）。

    out_dir 默认 <数据根>/src/papers。
    """
    tpl = PROJECT_ROOT / "templates" / "reading-note.tex"
    content = tpl.read_text(encoding="utf-8")
    title = meta.get("title") or Path(str(meta.get("url", "note"))).name
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "_", title)[:60].strip("_") or "note"
    authors = meta.get("authors") or []
    author = (authors[0] if authors else "作者")
    today = datetime.date.today().isoformat()
    if out_dir is None:
        out_dir = str(Config.load().data_dir / "src" / "papers")
    out_dir = os.path.expanduser(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{today}_{slug}.tex")
    meta_line = " | ".join(filter(None, [
        meta.get("arxiv_id") or "", meta.get("doi") or "",
        author, str(meta.get("year", ""))]))
    content = (content.replace("%%TITLE%%", title)
                      .replace("%%META%%", meta_line)
                      .replace("%%DATE%%", today))
    if not os.path.exists(out):
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)
    return out
