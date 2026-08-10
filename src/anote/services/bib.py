"""引用库领域服务：refs.bib 解析与引用链路校验。"""
from __future__ import annotations

import os
import re
from pathlib import Path

from ..core import Config

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
