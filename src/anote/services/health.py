"""健康检查领域服务：Anote 一致性自检（7 项）——check.py 的业务逻辑。

返回 [(ok: bool, msg: str)]；ok=False 为需处理项。
"""
from __future__ import annotations

import datetime
import os
import re
from pathlib import Path

from ..core import Config
from .bib import BibService
from .notes import NotesService


class HealthService:
    def __init__(self, data_dir: Path):
        self.data = Path(data_dir)

    def run(self) -> list[tuple[bool, str]]:
        results: list[tuple[bool, str]] = []
        results.append(self.check_unregistered())
        results.append(self.check_queue_notes())
        results.append(self.check_pdf_orphans())
        results.append(self.check_memory_freshness())
        results.append(self.check_projects())
        results.append(self.check_meta())
        results.append(self.check_bib())
        results.append(self.check_docs())
        return results

    # ---- 1. 未登记索引 ----
    def check_unregistered(self) -> tuple[bool, str]:
        src = self.data / "src"
        unreg = []
        for root, _, files in os.walk(src):
            for f in files:
                if f.endswith(".tex") and f != "00-index.tex":
                    idx = Path(root) / "00-index.tex"
                    if idx.exists() and f not in idx.read_text(encoding="utf-8", errors="ignore") \
                            and f.replace("_", r"\_") not in idx.read_text(encoding="utf-8", errors="ignore"):
                        unreg.append(str(Path(root).relative_to(self.data)))
        if unreg:
            return False, f"[1] 未登记到 00-index 的笔记 ({len(unreg)}): {unreg[:5]}"
        return True, "[1] ✓ 所有笔记均已登记"

    # ---- 2. 队列缺笔记 ----
    def check_queue_notes(self) -> tuple[bool, str]:
        q = (self.data / "queue.md")
        if not q.exists():
            return True, "[2] ✓ queue.md 不存在（无需检查）"
        text = q.read_text(encoding="utf-8", errors="ignore")
        done = re.findall(r"✅[^\n]*\|\s*(src/papers/[^|\s]+)", text)
        missing = [d for d in done if not (self.data / d).exists()]
        if missing:
            return False, f"[2] 队列标记已精读但笔记缺失: {missing}"
        return True, "[2] ✓ 已精读论文均有笔记"

    # ---- 3. PDF 孤儿 ----
    def check_pdf_orphans(self) -> tuple[bool, str]:
        pdf_dir = self.data / "pdfs"
        if not pdf_dir.is_dir():
            return True, "[3] ✓ pdfs/ 为空或不存在"
        q_text = (self.data / "queue.md").read_text(encoding="utf-8", errors="ignore") \
            if (self.data / "queue.md").exists() else ""
        orphans = [f for f in os.listdir(pdf_dir)
                   if f.endswith(".pdf") and f.replace(".pdf", "") not in q_text]
        if orphans:
            return False, f"[3] pdfs/ 中 {len(orphans)} 个 PDF 未登记到队列: {orphans[:5]}"
        return True, "[3] ✓ PDF 附件均有队列条目"

    # ---- 4. 记忆层新鲜度 ----
    def check_memory_freshness(self) -> tuple[bool, str]:
        limits = {"research-log.md": 45, "insights.md": 120,
                  "open-questions.md": 180, "concepts.md": 180}
        stale = []
        for name, max_days in limits.items():
            p = self.data / "memory" / name
            if not p.exists():
                stale.append(f"{name} 缺失")
                continue
            age = (datetime.datetime.now()
                   - datetime.datetime.fromtimestamp(p.stat().st_mtime)).days
            if age > max_days:
                stale.append(f"{name} {age}天未更新")
        if stale:
            return False, f"[4] 记忆层: {stale}"
        return True, "[4] ✓ 记忆层更新正常"

    # ---- 5. 项目结构 ----
    def check_projects(self) -> tuple[bool, str]:
        pd = self.data / "projects"
        bad = []
        if pd.is_dir():
            for d in sorted(p for p in pd.iterdir() if p.is_dir() and not p.name.startswith("_")):
                for need in ("plan.tex", "log.tex"):
                    if not (d / need).exists():
                        bad.append(f"{d.name}/ 缺 {need}")
        if bad:
            return False, f"[5] 项目结构: {bad[:5]}"
        return True, "[5] ✓ 项目结构检查完成"

    # ---- 6. META ----
    def check_meta(self) -> tuple[bool, str]:
        missing = [n.rel for n in NotesService(self.data).scan() if not n.meta]
        if missing:
            return False, f"[6] {len(missing)} 篇笔记缺 META: {missing[:5]}（anote meta 查看）"
        return True, "[6] ✓ 笔记均有 META 元数据"

    # ---- 7. 引用链路 ----
    def check_docs(self) -> tuple[bool, str]:
        """文档登记一致性：pdfs/ebooks 有文件未登记；登记条目文件缺失。"""
        from .docs import DocService
        svc = DocService(self.data)
        entries = svc.load()
        reg_paths = {e.path for e in entries}
        missing = [e.path for e in entries if not (self.data / e.path).exists()]
        unreg = []
        for d in ("pdfs", "ebooks"):
            dd = self.data / d
            if dd.is_dir():
                for p in sorted(dd.rglob("*")):
                    if p.is_file() and p.suffix.lower() in (".pdf", ".epub", ".mobi", ".azw3") \
                            and not p.name.startswith(".") and str(p.relative_to(self.data)) not in reg_paths:
                        unreg.append(str(p.relative_to(self.data)))
        if missing or unreg:
            return False, f"[8] 文档登记不一致: 缺失 {len(missing)} 个, 未登记 {len(unreg)} 个"
        return True, f"[8] ✓ 文档登记一致（{len(entries)} 条）"

    def check_bib(self) -> tuple[bool, str]:
        bib = BibService(self.data)
        if not bib.refs.exists():
            return False, "[7] refs.bib 不存在（Zotero 导出，见 anote zotero setup）"
        missing = bib.missing()
        if missing:
            return False, f"[7] 笔记引用了 {len(missing)} 个不在 refs.bib 的键: {missing[:8]}"
        return True, f"[7] ✓ 引用链路正常（{len(bib.keys())} 条目）"
