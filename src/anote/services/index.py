from __future__ import annotations

"""索引生成领域服务：扫描 src/ 生成分层 00-index.tex。"""

import os
import re
import sys


from pathlib import Path

INDEX_TMPL = r"""%% ===== 索引（由 index-gen.py 自动生成，勿手改）=====
\documentclass[11pt]{ctexart}
\usepackage[margin=2.5cm]{geometry}
\usepackage{paralist,hyperref}
\title{%(title)s}
\date{\today}

\begin{document}
\maketitle
\tableofcontents
%(sections)s
\end{document}
"""


def escape(s):
    return re.sub(r"[_&%#$]", r"\\\g<0>", s)


def walk_notes(src):
    """返回 {dir: {subdirs:[], notes:[], papers:[]}}"""
    tree = {}
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in sorted(dirs) if not d.startswith("_")]
        rel = os.path.relpath(root, src)
        tree[rel] = {
            "subdirs": [d for d in dirs],
            "notes": sorted(f for f in files if f.endswith(".tex") and f != "00-index.tex"),
            "papers": sorted(f for f in files if f.endswith(".tex") and f != "00-index.tex"),
        }
    return tree


def title_of(dirname):
    return dirname if dirname != "." else "笔记总索引"


def gen_index(rel, tree, src):
    node = tree[rel]
    parts = []
    # 子目录
    if node["subdirs"]:
        parts.append("\\section{子学科}")
        parts.append("\\begin{compactitem}")
        for d in node["subdirs"]:
            parts.append(f"\\item \\texttt{{{escape(d)}/}}（见下节或 \\texttt{{{escape(os.path.join(rel, d))}/00-index.tex}}）")
        parts.append("\\end{compactitem}")
    # 笔记
    if node["notes"]:
        parts.append("\\section{笔记}")
        parts.append("\\begin{compactitem}")
        for n in node["notes"]:
            base = os.path.splitext(n)[0]
            parts.append(f"\\item \\texttt{{{escape(n)}}}")
        parts.append("\\end{compactitem}")
    # 子学科索引内容（嵌套）
    for d in node["subdirs"]:
        sub_rel = os.path.join(rel, d)
        if sub_rel in tree and (tree[sub_rel]["notes"] or tree[sub_rel]["subdirs"]):
            parts.append(f"\\section{{{escape(title_of(d))}}}")
            parts.append(f"\\input{{{escape(os.path.join(rel, d, '00-index.tex'))}}}")
    return INDEX_TMPL % {"title": escape(title_of(rel)), "sections": "\n".join(parts)}


