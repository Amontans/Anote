#!/usr/bin/env python3
"""Anote 统计：输出各类文件数（anote stats）。"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anote_config import data_dir as cfg_data_dir  # noqa: E402

EXCLUDE = {".semantic", ".venv", ".git"}


def count_files(root, exts, exclude_dirs=(), skip_names=()):
    n = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE and d not in exclude_dirs]
        for f in filenames:
            if f in skip_names:
                continue
            if f.endswith(exts):
                n += 1
    return n


def count_dirs(root, skip=("_template", "00-projects-index.tex")):
    if not os.path.isdir(root):
        return 0
    return sum(1 for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and d not in skip)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    data = cfg_data_dir()

    def c(rel, exts, **kw):
        return count_files(os.path.join(data, rel), exts, **kw)

    src = os.path.join(data, "src")
    stats = {
        "笔记总数": c("src", (".tex", ".md"), skip_names=("00-index.tex", "README.md")),
        "论文精读": c("src/papers", ".tex", skip_names=("00-index.tex",)),
        "教科书": count_dirs(os.path.join(data, "books")),
        "章节": c("books", ".tex"),
        "项目": count_dirs(os.path.join(data, "projects")),
        "回顾草稿": c("memory/reviews", ".md"),
        "PDF 附件": c("pdfs", ".pdf"),
        "编译产物 PDF": count_files(os.path.join(data, "books"), ".pdf"),
    }
    # 队列
    try:
        q = open(os.path.join(data, "queue.md"), encoding="utf-8").read()
        qs = {k: q.count(k) for k in ("📥", "📖", "✅", "🗄")}
    except Exception:  # noqa: BLE001
        qs = {"📥": 0, "📖": 0, "✅": 0, "🗄": 0}
    # 记忆条目
    mem_entries = 0
    for n in ("research-log.md", "insights.md", "concepts.md", "open-questions.md"):
        try:
            mem_entries += sum(1 for l in open(os.path.join(data, "memory", n), encoding="utf-8")
                               if l.startswith("- "))
        except Exception:  # noqa: BLE001
            pass

    if a.json:
        import json
        print(json.dumps({**stats, "队列": qs, "记忆条目": mem_entries}, ensure_ascii=False, indent=2))
        return

    print(f"数据目录: {data}\n")
    print(f"  📝 笔记总数     {stats['笔记总数']}")
    print(f"  📄 论文精读     {stats['论文精读']}")
    print(f"  📚 教科书       {stats['教科书']}（章节 {stats['章节']}）")
    print(f"  📁 项目         {stats['项目']}")
    print(f"  🔄 回顾草稿     {stats['回顾草稿']}")
    print(f"  📥 队列         📥{qs['📥']} 📖{qs['📖']} ✅{qs['✅']} 🗄{qs['🗄']}")
    print(f"  🧠 记忆条目     {mem_entries}")
    print(f"  🗂️ PDF 附件     {stats['PDF 附件']}")
    print(f"  📦 编译产物 PDF {stats['编译产物 PDF']}")


if __name__ == "__main__":
    main()
