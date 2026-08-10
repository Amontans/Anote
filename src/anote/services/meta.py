"""META 元数据领域服务：完整性审计。"""
from __future__ import annotations

from .notes import NotesService

REQUIRED = ("学科", "日期")
SUGGESTED = ("标签", "来源")


def audit(notes) -> tuple[list, list]:
    """返回 (缺 META 的笔记, [(note, 缺字段)])."""
    missing_meta = [n for n in notes if not n.meta]
    missing_fields = []
    for n in notes:
        if n.meta:
            for f in REQUIRED + SUGGESTED:
                if not n.meta.get(f):
                    missing_fields.append((n, f))
    return missing_meta, missing_fields
