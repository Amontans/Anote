"""Anote 领域服务包（v1.6 模块化：一个领域一个模块）。

向后兼容：旧 import（from anote.services import X）继续可用。
新增领域 → 新建模块 + 在此重导出。
注意：语义/检索等重型模块按需 import（避免核心依赖 numpy/fastembed）。
"""
from .queue import QueueEntry, QueueService
from .notes import Note, NotesService
from .stats import StatsService
from .bib import BibService
from .health import HealthService
from . import (queue, notes, stats, bib, health, backup, bootstrap, docs,
               ebooks, graph, index, mdview, meta, migration, papers, preview,
               restore, review, webserver, wiki, zotero)

__all__ = ["QueueEntry", "QueueService", "Note", "NotesService",
           "StatsService", "BibService", "HealthService",
           "queue", "notes", "stats", "bib", "health", "backup", "bootstrap",
           "docs", "ebooks", "graph", "index", "mdview", "meta",
           "migration", "papers", "preview", "restore", "review",
           "webserver", "wiki", "zotero"]
