"""统计领域服务：各类文件数。"""
from __future__ import annotations

import os
from pathlib import Path

from ..core import Config
from .queue import QueueService

class StatsService:
    """统计各类文件数（anote stats）。"""

    def __init__(self, data_dir: Path):
        self.data = Path(data_dir)

    def compute(self) -> dict:
        def count(rel: str, exts: tuple, skip=()) -> int:
            root = self.data / rel
            n = 0
            if root.is_dir():
                for r, _, fs in os.walk(root):
                    for f in fs:
                        if f in skip:
                            continue
                        if f.endswith(exts):
                            n += 1
            return n

        def dirs(rel: str, skip=("_template",)) -> int:
            root = self.data / rel
            if not root.is_dir():
                return 0
            return sum(1 for d in os.listdir(root)
                       if (root / d).is_dir() and d not in skip)

        q = QueueService(self.data).counts()
        return {
            "笔记总数": count("src", (".tex", ".md"), skip=("00-index.tex", "README.md")),
            "论文精读": count("src/papers", ".tex", skip=("00-index.tex",)),
            "教科书": dirs("books"),
            "章节": count("books", ".tex"),
            "项目": dirs("projects"),
            "回顾草稿": count("memory/reviews", ".md"),
            "PDF 附件": count("pdfs", ".pdf"),
            "编译产物 PDF": count("books", ".pdf"),
            "队列": q,
        }
