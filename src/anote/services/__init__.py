"""Anote 领域服务包（v1.6 模块化：一个领域一个模块）。

向后兼容：旧 import（from anote.services import X）继续可用。
新增领域 → 新建模块 + 在此重导出。
"""
from .queue import QueueEntry, QueueService
from .notes import Note, NotesService
from .stats import StatsService
from .bib import BibService
from . import queue, notes, stats, bib

__all__ = ["QueueEntry", "QueueService", "Note", "NotesService",
           "StatsService", "BibService", "queue", "notes", "stats", "bib"]
