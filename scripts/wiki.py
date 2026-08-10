#!/usr/bin/env python3
"""anote wiki —— 知识编译层（v1.4，LLM Wiki 范式）：把 src/ 笔记按学科/分支编译成主题页。

L1 主题页 → wiki/<学科>_<分支>.md（MD 派生产物，可重建；经 Pi 生成，你确认）。

接口声明（契约）:
    输入: argv: [--dry] [--branch <学科>/<分支>] [--force]
    输出: stdout=编译报告；stderr=错误；退出码 0/1
    副作用: --dry 无；正常模式写 wiki/*.md
"""
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config, ai_ask  # noqa: E402
from anote.services import NotesService  # noqa: E402


def group_notes(notes) -> dict[tuple[str, str], list]:
    """按 (学科, 分支) 分组笔记（纯函数，可单测）。"""
    groups = defaultdict(list)
    for n in notes:
        disc = n.meta.get("学科") or ""
        branch = n.meta.get("分支") or ""
        if not disc and not branch:
            # 按目录推断：src/<学科>/<分支>/...
            parts = n.rel.split("/")
            disc = parts[1] if len(parts) > 1 else ""
            branch = parts[2] if len(parts) > 2 else ""
        groups[(disc, branch)].append(n)
    return dict(groups)


PROMPT = """你是 Anote 知识编译引擎。请把以下学习笔记编译成一个结构化的【学科主题页】。

学科: {disc} | 分支: {branch}

笔记清单（标题 + 内容开头）:
{notes}

主题页结构（Markdown）:
# {disc} - {branch}
## 概览（这个分支在学什么，核心概念关系，一段话）
## 核心概念（每个概念 1-2 行）
## 方法与定理（名称：一句话，来源笔记）
## 关键文献（如有）
## 未解决问题（如有）
## 学习进度（已覆盖 / 待补）

要求: 忠实于笔记内容，不虚构；输出完整 Markdown，不要额外解释。
"""


def main() -> int:
    args = sys.argv[1:]
    dry = "--dry" in args
    force = "--force" in args
    branch_filter = None
    if "--branch" in args:
        i = args.index("--branch")
        if i + 1 < len(args):
            branch_filter = args[i + 1]

    data = Config.load().data_dir
    notes = NotesService(data).scan()
    groups = group_notes(notes)
    if branch_filter:
        disc, _, branch = branch_filter.partition("/")
        groups = {k: v for k, v in groups.items() if k[0] == disc and (not branch or k[1] == branch)}

    wiki_dir = Path(data) / "wiki"
    print(f"知识编译计划（{len(groups)} 个主题）")
    for (disc, branch), ns in sorted(groups.items()):
        print(f"  • {disc or '?'}/{branch or '?'}: {len(ns)} 篇")
    if dry:
        print("\n（--dry：未生成，实际编译将写入 wiki/ 并经 Pi 生成）")
        return 0

    wiki_dir.mkdir(exist_ok=True)
    for (disc, branch), ns in sorted(groups.items()):
        out = wiki_dir / f"{disc}_{branch}.md"
        if out.exists() and not force:
            print(f"  ⏭ {out.name} 已存在（--force 重建）")
            continue
        notes_block = "\n".join(
            f"- {n.title}：{(Path(data) / n.rel).read_text(encoding='utf-8', errors='ignore')[:300].strip()}"
            for n in ns)
        r = ai_ask(PROMPT.format(disc=disc or "未分类", branch=branch or "未分类", notes=notes_block))
        if not r.ok:
            print(f"  ✗ {disc}/{branch}: Pi 调用失败 {r.stderr}")
            continue
        out.write_text(r.stdout + "\n", encoding="utf-8")
        print(f"  ✓ 已生成 {out.relative_to(data)}")
    print("\n完成。请人工确认主题页内容（AI 只负责草拟）。")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
