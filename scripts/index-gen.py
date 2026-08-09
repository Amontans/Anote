#!/usr/bin/env python3
"""分层学科索引生成器：扫描 src/ 自动生成/更新各层 00-index.tex。

用法:
  index-gen.py              # 扫描 ~/Projects/notes/src 全量更新
  index-gen.py --dry        # 只打印将生成哪些索引
"""
import sys
import argparse
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anote_config import data_dir as _cfg_data_dir
DEFAULT_NOTES = _cfg_data_dir()

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notes", default=DEFAULT_NOTES)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    src = os.path.join(os.path.expanduser(a.notes), "src")
    if not os.path.isdir(src):
        print(f"未找到 {src}")
        sys.exit(1)
    tree = walk_notes(src)
    for rel in sorted(tree, key=lambda r: r.count(os.sep)):
        if rel == "." or (tree[rel]["notes"] or tree[rel]["subdirs"]):
            out = os.path.join(src, rel, "00-index.tex")
            content = gen_index(rel, tree, src)
            if a.dry:
                print(f"[dry] {out} ({len(content)} bytes)")
            else:
                with open(out, "w") as f:
                    f.write(content)
                print(f"✓ {out}")
    print("完成。新增笔记后重跑本脚本更新索引。")


if __name__ == "__main__":
    import sys
    main()
