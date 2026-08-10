"""队列领域服务：queue.md 解析/更新/统计。"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..core import Config

STATUSES = ("📥", "📖", "✅", "🗄")

@dataclass
class QueueEntry:
    line: str
    status: str
    date: str
    title: str
    key: str
    note: str

    def with_status(self, new_status: str) -> str:
        return self.line.replace(f"| {self.status} |", f"| {new_status} |", 1)

class QueueService:
    """queue.md 的解析/更新/统计（单一实现）。"""

    ROW = re.compile(r"^\|\s*(📥|📖|✅|🗄)\s*\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\s*\|")

    def __init__(self, data_dir: Path):
        self.path = Path(data_dir) / "queue.md"

    def read_entries(self) -> list[QueueEntry]:
        if not self.path.exists():
            return []
        entries = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            m = self.ROW.match(line)
            if m:
                entries.append(QueueEntry(line, m.group(1), m.group(2).strip(),
                                          m.group(3).strip(), m.group(4).strip(), m.group(5).strip()))
        return entries

    def counts(self) -> dict[str, int]:
        return {s: sum(1 for e in self.read_entries() if e.status == s) for s in STATUSES}

    def update_line(self, old_line: str, new_line: str) -> bool:
        if not self.path.exists():
            return False
        text = self.path.read_text(encoding="utf-8")
        if old_line not in text:
            return False
        self.path.write_text(text.replace(old_line, new_line, 1), encoding="utf-8")
        return True

    def cycle_status(self, entry: QueueEntry) -> str:
        nxt = STATUSES[(STATUSES.index(entry.status) + 1) % len(STATUSES)]
        self.update_line(entry.line, entry.with_status(nxt))
        return nxt
