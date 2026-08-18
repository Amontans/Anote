"""笔记领域服务：src/ 扫描与 META 提取/过滤/新建。"""
from __future__ import annotations

import datetime
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ..core import PROJECT_ROOT, Config

META_PATTERN = re.compile(r"==META==\s*(.*)")


def latex_escape(text: str) -> str:
    """转义 LaTeX 正文中的特殊字符（保持中文/空格）。"""
    repl = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%",
            "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
            "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(repl.get(c, c) for c in text)


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
            dirnames[:] = [d for d in dirnames if not d.startswith((".", "_"))]
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

    def create(self, subject_path: str, title: str, template: str = "note",
               data_dir: Path | None = None, open_editor: bool = False) -> Path:
        """按模板新建笔记。返回创建的文件路径；同名文件绝不覆盖。"""
        data = Path(data_dir) if data_dir else Config.load().data_dir
        title = title.strip()
        subject_path = subject_path.strip().strip("/")
        if not subject_path or not title:
            raise ValueError("用法: anote new <学科/分支> <标题>")
        for part in subject_path.split("/"):
            if part in ("", ".", ".."):
                raise ValueError(f"非法学科/分支: {subject_path}")

        parts = subject_path.split("/")
        disc = parts[0]
        branch = "/".join(parts[1:])
        tpl = PROJECT_ROOT / "templates" / f"{template}.tex"
        if not tpl.exists():
            tpl = PROJECT_ROOT / "templates" / "note.tex"
            template = "note"
        today = datetime.date.today().isoformat()
        safe_title = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", title).strip("._")
        fname = f"{today}_{safe_title}.tex"
        dest_dir = data / "src" / subject_path
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / fname
        if dest.exists():
            raise FileExistsError(f"笔记已存在（未覆盖）: {dest}")

        content = (tpl.read_text(encoding="utf-8")
                   .replace("%%DISC%%", disc)
                   .replace("%%BRANCH%%", branch)
                   .replace("%%TITLE%%", latex_escape(title))
                   .replace("%%DATE%%", today))
        dest.write_text(content, encoding="utf-8")
        if open_editor:
            editor = Config.load().editor
            subprocess.Popen([editor, str(dest)], start_new_session=True)
        return dest
