"""Zotero 集成领域服务：BBT 检测 / 库统计 / refs.bib 解析。"""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path

ZOTERO_DATA = Path("~/Zotero").expanduser()
ZOTERO_PROFILE = Path("~/.zotero/zotero").expanduser()
BIB_ENTRY = re.compile(r"@(\w+)\{([^,]+),", re.M)


def bbt_installed() -> str:
    """检测 Better BibTeX 插件。"""
    if ZOTERO_PROFILE.is_dir():
        for p in ZOTERO_PROFILE.rglob("extensions.json"):
            if "better-bibtex" in p.read_text(encoding="utf-8", errors="ignore"):
                return "✓ 已安装"
    return ""


def library_count() -> int:
    """只读 Zotero 库条目数（-1 未初始化 / -2 读取失败）。"""
    db = ZOTERO_DATA / "zotero.sqlite"
    if not db.exists():
        return -1
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        n = con.execute("SELECT COUNT(*) FROM items WHERE itemTypeID NOT IN (1,14)").fetchone()[0]
        con.close()
        return n
    except Exception:  # noqa: BLE001
        return -2


def parse_bib(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [(m.group(1), m.group(2).strip()) for m in BIB_ENTRY.finditer(text)]
