"""知识图谱领域服务：META 标签 → 引用笔记聚合。"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .notes import NotesService


def build_graph(data: Path, limit: int = 20) -> dict:
    notes = NotesService(data).scan()
    g: dict = defaultdict(list)
    for n in notes:
        tags = [t.strip() for t in (n.meta.get("标签") or "").split(",") if t.strip()]
        for t in tags:
            g[t].append((n.rel, 1))
    return {k: sorted(v, key=lambda x: -x[1])[:limit] for k, v in sorted(g.items())}
