#!/usr/bin/env python3
"""知识库一致性自检：发现长期使用中的结构问题。

检查项:
  1. src/ 下未被 00-index.tex 登记的笔记
  2. queue.md 中标记已精读但无笔记文件的条目
  3. pdfs/ 中有 PDF 但队列中无对应条目的文件
  4. memory/ 各文件最后修改时间（长期未更新告警）
  5. projects/ 项目缺少 plan.tex 或 log.tex
用法: check.py [--notes DIR]
"""
import sys
import argparse
import datetime
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anote_config import data_dir as _cfg_data_dir
DEFAULT_NOTES = _cfg_data_dir()
WARN = []

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote import cli as _cli  # noqa: E402

def read(path):
    try:
        return open(path, encoding="utf-8").read()
    except Exception:  # noqa: BLE001
        return ""


def check_1_unregistered(notes):
    src = os.path.join(notes, "src")
    unreg = []
    for root, _, files in os.walk(src):
        for f in files:
            if f.endswith(".tex") and f != "00-index.tex":
                # 检查父目录的 00-index.tex（嵌套索引）
                idx = os.path.join(root, "00-index.tex")
                if os.path.exists(idx) and f not in read(idx) and f.replace("_", r"\_") not in read(idx):
                    unreg.append(os.path.relpath(os.path.join(root, f), notes))
    if unreg:
        WARN.append(f"[1] 未登记到 00-index 的笔记 ({len(unreg)}):\n    " + "\n    ".join(unreg))
    else:
        print("[1] ✓ 所有笔记均已登记")


def check_2_queue_notes(notes):
    q = read(os.path.join(notes, "queue.md"))
    done = re.findall(r"✅.*?\\texttt\{src/papers/([^}]+)\}", q)
    missing = [d for d in done if not os.path.exists(os.path.join(notes, "src/papers", d))]
    if missing:
        WARN.append(f"[2] 队列标记已精读但笔记缺失 ({len(missing)}): {missing}")
    else:
        print("[2] ✓ 已精读论文均有笔记")


def check_3_pdfs(notes):
    pdf_dir = os.path.join(notes, "pdfs")
    if not os.path.isdir(pdf_dir):
        print("[3] ✓ pdfs/ 目录为空或不存在")
        return
    q = read(os.path.join(notes, "queue.md"))
    orphans = [f for f in os.listdir(pdf_dir)
               if f.endswith(".pdf") and f.replace(".pdf", "") not in q]
    if orphans:
        WARN.append(f"[3] pdfs/ 中 {len(orphans)} 个 PDF 未登记到队列")
    else:
        print("[3] ✓ PDF 附件均有队列条目")


def check_4_memory_freshness(notes):
    for name, max_days in [("research-log.md", 45), ("insights.md", 120),
                           ("open-questions.md", 180), ("concepts.md", 180)]:
        p = os.path.join(notes, "memory", name)
        if not os.path.exists(p):
            WARN.append(f"[4] memory/{name} 缺失")
            continue
        age = (datetime.datetime.now()
               - datetime.datetime.fromtimestamp(os.path.getmtime(p))).days
        if age > max_days:
            WARN.append(f"[4] memory/{name} 已 {age} 天未更新（> {max_days}）")
    if not any(w.startswith("[4]") for w in WARN):
        print("[4] ✓ 记忆层更新正常")


def check_5_projects(notes):
    pd = os.path.join(notes, "projects")
    for d in sorted(os.listdir(pd)):
        if d.startswith("_") or d.startswith("00"):
            continue
        for need in ("plan.tex", "log.tex"):
            if not os.path.exists(os.path.join(pd, d, need)):
                WARN.append(f"[5] projects/{d}/ 缺少 {need}")
    print("[5] ✓ 项目结构检查完成")




def check_6_meta(notes):
    """检查 src/ 下笔记是否含 META 元数据块（多学科规范）。"""
    missing = []
    for root, _, files in os.walk(os.path.join(notes, "src")):
        for f in files:
            if f.endswith(".tex") and f != "00-index.tex":
                p = os.path.join(root, f)
                head = read(p)[:300]
                if "==META==" not in head:
                    missing.append(os.path.relpath(p, notes))
    if missing:
        WARN.append(f"[6] {len(missing)} 篇笔记缺 META 元数据（学科/标签）：\n    " + "\n    ".join(missing[:10]))
    else:
        print("[6] ✓ 笔记均有 META 元数据")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notes", default=DEFAULT_NOTES)
    a = ap.parse_args()
    notes = os.path.expanduser(a.notes)
    print(f"=== 知识库自检: {notes} ===")
    check_1_unregistered(notes)
    check_2_queue_notes(notes)
    check_3_pdfs(notes)
    check_4_memory_freshness(notes)
    check_5_projects(notes)
    check_6_meta(notes)
    print("\n=== 结果 ===")
    if WARN:
        for w in WARN:
            print("⚠️", w)
        print(f"\n共 {len(WARN)} 项需处理（可让 Pi 协助修复）")
    else:
        print("✅ 全部正常")


if __name__ == "__main__":
    sys.exit(_cli.run(main))
