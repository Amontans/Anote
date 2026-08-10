"""笔记领域服务：src/ 扫描与 META 提取/过滤。"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..core import Config

META_PATTERN = re.compile(r"==META==\s*(.*)")

@dataclass
class Note:
    path: Path
    rel: str
    title: str
    meta: dict = field(default_factory=dict)

class NotesService:
    """src/ 笔记扫描与 META 提取。"""

    SKIP = {"00-index.tex", "README.md"}

    def __init__(self, data_dir: Path):
        self.src = Path(data_dir) / "src"

    def scan(self) -> list[Note]:
        notes = []
        if not self.src.is_dir():
            return notes
        for dirpath, dirnames, filenames in os.walk(self.src):
            dirnames[:] = [d for d in dirnames if not d.startswith("_")]
            for f in sorted(filenames):
                if f in self.SKIP or not f.endswith((".tex", ".md")):
                    continue
                p = Path(dirpath) / f
                rel = str(p.relative_to(self.src.parent))
                notes.append(Note(p, rel, f, self.meta_of(p)))
        return notes

    def meta_of(self, path: Path) -> dict:
        try:
            head = path.read_text(encoding="utf-8")[:400]
        except OSError:
            return {}
        m = META_PATTERN.search(head)
        if not m:
            return {}
        meta = {}
        for part in m.group(1).split("|"):
            if ":" in part:
                k, _, v = part.partition(":")
                meta[k.strip()] = v.strip()
        return meta

    def filter(self, term: str) -> list[Note]:
        t = term.strip().lower()
        if not t:
            return self.scan()
        out = []
        for n in self.scan():
            if t in n.rel.lower() or t in n.title.lower():
                out.append(n)
                continue
            if any(t in v.lower() for v in n.meta.values()):
                out.append(n)
        return out
