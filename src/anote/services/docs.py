"""文档管理领域服务：docs/registry.md 登记表（阅读管理核心，契约见 INTERFACES）。

专业图书管理要素：状态机 / 元数据 / 去重(sha256) / 进度 / 最后阅读 / 导入 / 统计。
"""
from __future__ import annotations

import datetime
import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

STATUSES = ("📥", "📖", "✅", "🗄")
COLS = ["状态", "类型", "文件", "标题", "作者", "年份", "标签", "笔记", "进度", "最后阅读", "哈希"]
ROW_RE = re.compile(r"^\|\s*(📥|📖|✅|🗄)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|")


@dataclass
class DocEntry:
    status: str = "📥"
    doc_type: str = ""
    path: str = ""
    title: str = ""
    author: str = ""
    year: str = ""
    tags: str = ""
    note: str = ""
    progress: str = "0%"
    last_read: str = "-"
    hash8: str = ""

    def row(self) -> str:
        vals = [self.status, self.doc_type, self.path, self.title, self.author, self.year,
                self.tags, self.note, self.progress, self.last_read, self.hash8]
        return "| " + " | ".join(v.strip() for v in vals) + " |"


def sha8(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:8]


class DocService:
    def __init__(self, data_dir: Path):
        self.data = Path(data_dir)
        self.registry = self.data / "docs" / "registry.md"

    def _ensure(self):
        self.registry.parent.mkdir(parents=True, exist_ok=True)
        if not self.registry.exists():
            self.registry.write_text(
                "# 文档登记表（registry）\n\n"
                + "| " + " | ".join(COLS) + " |\n"
                + "|" + "---|" * len(COLS) + "\n", encoding="utf-8")

    def load(self) -> list[DocEntry]:
        self._ensure()
        entries = []
        for line in self.registry.read_text(encoding="utf-8").splitlines():
            m = ROW_RE.match(line)
            if m:
                entries.append(DocEntry(m.group(1), m.group(2).strip(), m.group(3).strip(),
                                        m.group(4).strip(), m.group(5).strip(), m.group(6).strip(),
                                        m.group(7).strip(), m.group(8).strip(), m.group(9).strip(),
                                        m.group(10).strip(), m.group(11).strip()))
        return entries

    def save(self, entries: list[DocEntry]) -> None:
        self._ensure()
        lines = ["# 文档登记表（registry）", "",
                 "| " + " | ".join(COLS) + " |", "|" + "---|" * len(COLS)]
        lines += [e.row() for e in entries]
        self.registry.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def find(self, path: str) -> DocEntry | None:
        for e in self.load():
            if e.path == path:
                return e
        return None

    def add(self, file_rel: str, meta: dict | None = None) -> tuple[bool, str]:
        """登记文档（sha256 去重）。返回 (成功, 信息)。"""
        p = self.data / file_rel
        if not p.exists():
            return False, f"文件不存在: {file_rel}"
        entries = self.load()
        h = sha8(p)
        for e in entries:
            if e.hash8 == h:
                return False, f"已存在（sha256 相同）: {e.path}"
            if e.path == file_rel:
                return False, f"路径已登记: {file_rel}"
        meta = meta or {}
        ext = p.suffix.lower().lstrip(".")
        entries.append(DocEntry(
            status=meta.get("status", "📥"),
            doc_type=meta.get("type", ext),
            path=file_rel,
            title=meta.get("title", p.stem),
            author=meta.get("author", ""),
            year=meta.get("year", ""),
            tags=meta.get("tags", ""),
            note=meta.get("note", ""),
            progress="0%", last_read="-", hash8=h))
        self.save(entries)
        return True, f"✓ 已登记: {file_rel}"

    def update(self, file_rel: str, **fields) -> bool:
        entries = self.load()
        for e in entries:
            if e.path == file_rel:
                for k, v in fields.items():
                    if hasattr(e, k):
                        setattr(e, k, str(v))
                self.save(entries)
                return True
        return False

    def progress(self, file_rel: str, pct: str) -> bool:
        today = datetime.date.today().isoformat()
        return self.update(file_rel, progress=pct, last_read=today)

    def mark_read(self, file_rel: str) -> None:
        """阅读登记：未登记→自动加；📥→📖；更新最后阅读。"""
        if not self.find(file_rel):
            self.add(file_rel)
        e = self.find(file_rel)
        if e and e.status == "📥":
            self.update(file_rel, status="📖")
        self.update(file_rel, last_read=datetime.date.today().isoformat())

    def stats(self) -> dict:
        entries = self.load()
        by_status = {s: sum(1 for e in entries if e.status == s) for s in STATUSES}
        by_type = {}
        for e in entries:
            by_type[e.doc_type or "?"] = by_type.get(e.doc_type or "?", 0) + 1
        return {"total": len(entries), "status": by_status, "types": by_type,
                "unread_ratio": round(by_status.get("📥", 0) / max(1, len(entries)), 2)}

    def filter(self, status: str = "", tag: str = "", doc_type: str = "",
               sort: str = "title") -> list[DocEntry]:
        out = self.load()
        if status:
            out = [e for e in out if e.status == status]
        if tag:
            out = [e for e in out if tag in e.tags]
        if doc_type:
            out = [e for e in out if e.doc_type == doc_type]
        key = {"title": lambda e: e.title.lower(), "year": lambda e: e.year,
               "status": lambda e: e.status}[sort]
        return sorted(out, key=key)

    DOC_EXTS = (".pdf", ".epub", ".mobi", ".azw3")
    LIB_DIRS = ("pdfs", "ebooks")

    def import_dir(self, rel_dir: str = "") -> tuple[list[str], list[str]]:
        """批量扫描文档库（默认 pdfs/ ebooks/）→ 登记(排除派生.txt) + 提取文本。"""
        from .ebooks import extract_epub, extract_pdf_text
        dirs = [self.data / d for d in (self.LIB_DIRS if not rel_dir else [rel_dir])]
        added, extracted = [], []
        for base in dirs:
            if not base.is_dir():
                continue
            for root, _, files in os.walk(base):
                if any(part.startswith(".") for part in Path(root).parts[len(self.data.parts):]):
                    continue
                for f in sorted(files):
                    if f.startswith("."):
                        continue
                    p = Path(root) / f
                    ext = p.suffix.lower()
                    if ext not in self.DOC_EXTS:
                        continue
                    rel = str(p.relative_to(self.data))
                    if not self.find(rel):
                        ok, _ = self.add(rel)
                        if ok:
                            added.append(rel)
                    if ext == ".pdf" and not p.with_suffix(".txt").exists():
                        try:
                            extract_pdf_text(p)
                            extracted.append(rel)
                        except Exception:  # noqa: BLE001
                            pass
                    elif ext == ".epub" and not p.with_suffix(".txt").exists():
                        try:
                            p.with_suffix(".txt").write_text(extract_epub(p), encoding="utf-8")
                            extracted.append(rel)
                        except Exception:  # noqa: BLE001
                            pass
        return added, extracted
