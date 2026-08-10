"""知识编译领域服务：按学科/分支分组笔记并编译主题页。"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ..core import ai_ask

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


def group_notes(notes) -> dict:
    """按 (学科, 分支) 分组笔记（纯函数）。"""
    groups = defaultdict(list)
    for n in notes:
        disc = n.meta.get("学科") or ""
        branch = n.meta.get("分支") or ""
        if not disc and not branch:
            parts = n.rel.split("/")
            disc = parts[1] if len(parts) > 1 else ""
            branch = parts[2] if len(parts) > 2 else ""
        groups[(disc, branch)].append(n)
    return dict(groups)


def compile_theme(disc: str, branch: str, notes, data: Path, force: bool = False):
    """编译一个主题页 → 返回 (输出路径, 成功)。"""
    wiki_dir = Path(data) / "wiki"
    wiki_dir.mkdir(exist_ok=True)
    out = wiki_dir / f"{disc}_{branch}.md"
    if out.exists() and not force:
        return out, None  # 已存在，跳过
    notes_block = "\n".join(
        f"- {n.title}：{(Path(data) / n.rel).read_text(encoding='utf-8', errors='ignore')[:300].strip()}"
        for n in notes)
    r = ai_ask(PROMPT.format(disc=disc or "未分类", branch=branch or "未分类", notes=notes_block))
    if not r.ok:
        return out, r
    out.write_text(r.stdout + "\n", encoding="utf-8")
    return out, None
