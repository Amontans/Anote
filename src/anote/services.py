"""Anote 领域服务：队列/笔记/统计——TUI、CLI、脚本共用的单一真相源（DRY）。

所有对数据目录的读写经此层；表现层（TUI/scripts）不直接解析这些格式。
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .core import Config

STATUSES = ("📥", "📖", "✅", "🗄")
META_PATTERN = re.compile(r"==META==\s*(.*)")


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


@dataclass
class Note:
    path: Path
    rel: str
    title: str
    meta: dict = field(default_factory=dict)


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


class BibService:
    """refs.bib 引用库服务（解析/引用链路校验）——bibcheck/check/stats/MCP 共用。"""

    BIB_ENTRY = re.compile(r"@\w+\{([^,]+),", re.M)
    CITE = re.compile(r"\\cite[tp]?\*?\{([^}]+)\}")

    def __init__(self, data_dir: Path):
        self.refs = Path(data_dir) / "refs.bib"

    def keys(self) -> set[str]:
        if not self.refs.exists():
            return set()
        return {m.group(1).strip() for m in self.BIB_ENTRY.finditer(
            self.refs.read_text(encoding="utf-8", errors="ignore"))}

    def entries(self) -> list[tuple[str, str]]:
        if not self.refs.exists():
            return []
        text = self.refs.read_text(encoding="utf-8", errors="ignore")
        return [(m.group(0)[1:].split("{")[0], m.group(1).strip())
                for m in self.BIB_ENTRY.finditer(text)]

    def cited_keys(self) -> set[str]:
        """扫描 src 下 tex 的 cite 命令键。"""
        keys: set[str] = set()
        src = Path(self.refs).parent / "src"
        if src.is_dir():
            for root, _, fs in os.walk(src):
                for f in fs:
                    if not f.endswith(".tex"):
                        continue
                    try:
                        text = (Path(root) / f).read_text(encoding="utf-8", errors="ignore")
                    except OSError:
                        continue
                    for ln in text.splitlines():
                        if ln.strip().startswith("%"):  # 跳过 LaTeX 注释
                            continue
                        for m in self.CITE.finditer(ln):
                            keys.update(k.strip() for k in m.group(1).split(","))
        return keys

    def missing(self) -> list[str]:
        return sorted(self.cited_keys() - self.keys())

    def unused(self) -> list[str]:
        return sorted(self.keys() - self.cited_keys())
