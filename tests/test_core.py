#!/usr/bin/env python3
"""Anote 核心/服务单元测试（stdlib unittest，临时目录隔离，ANOTE_DATA env）。"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config, Result  # noqa: E402
from anote.services import BibService, NotesService, QueueService, StatsService  # noqa: E402


class TestConfig(unittest.TestCase):
    def test_env_override(self):
        with tempfile.TemporaryDirectory() as t:
            with patch.dict(os.environ, {"ANOTE_DATA": t}):
                cfg = Config.load()
                self.assertEqual(cfg.data_dir, Path(t))

    def test_save_set(self):
        with tempfile.TemporaryDirectory() as t:
            cfg_path = Path(t) / "config"
            with patch("anote.core.CONFIG_PATH", cfg_path):
                cfg = Config()
                cfg.set("editor", "vim")
                self.assertEqual(Config.load().editor, "vim")
                self.assertTrue(cfg_path.exists())

    def test_result(self):
        r = Result.success("ok")
        self.assertTrue(r.ok)
        self.assertEqual(r.tail, "ok")
        self.assertFalse(Result.failure("err").ok)


class TestQueueService(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        (self.dir / "queue.md").write_text(
            "# 队列\n\n| 状态 | 日期 | 论文 | ID | 笔记 |\n"
            "|------|------|------|----|------|\n"
            "| 📥 | 2026-08-09 | A | 1 | — |\n"
            "| ✅ | 2026-08-08 | B | 2 | src/papers/b.tex |\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_parse_and_counts(self):
        q = QueueService(self.dir)
        entries = q.read_entries()
        self.assertEqual(len(entries), 2)
        self.assertEqual(q.counts()["📥"], 1)
        self.assertEqual(q.counts()["✅"], 1)

    def test_cycle(self):
        q = QueueService(self.dir)
        e = q.read_entries()[0]
        nxt = q.cycle_status(e)
        self.assertEqual(nxt, "📖")
        self.assertIn("| 📖 |", (self.dir / "queue.md").read_text(encoding="utf-8"))


class TestNotesService(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        src = self.dir / "src" / "数学" / "代数"
        src.mkdir(parents=True)
        (src / "群论.tex").write_text(
            "% ==META== 学科: 数学 | 分支: 代数 | 标签: 群,环 | 日期: 2026-08-09 | 来源: 教材\n"
            "\\section{群}\n", encoding="utf-8")
        (src / "无META.tex").write_text("\\section{x}\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_scan_meta(self):
        s = NotesService(self.dir)
        notes = s.scan()
        self.assertEqual(len(notes), 2)
        meta = s.meta_of(self.dir / "src/数学/代数/群论.tex")
        self.assertEqual(meta.get("学科"), "数学")
        self.assertIn("环", meta.get("标签", ""))

    def test_filter(self):
        s = NotesService(self.dir)
        self.assertEqual(len(s.filter("环")), 1)
        self.assertEqual(len(s.filter("")), 2)


class TestStatsService(unittest.TestCase):
    def test_compute(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "src/数学").mkdir(parents=True)
            (d / "src/数学/a.tex").write_text("x", encoding="utf-8")
            (d / "memory/reviews").mkdir(parents=True)
            (d / "memory/reviews/r.md").write_text("y", encoding="utf-8")
            (d / "books").mkdir()
            (d / "books/我的书").mkdir()
            (d / "books/我的书/chapters").mkdir()
            (d / "books/我的书/chapters/ch01.tex").write_text("z", encoding="utf-8")
            st = StatsService(d).compute()
            self.assertEqual(st["笔记总数"], 1)
            self.assertEqual(st["教科书"], 1)
            self.assertEqual(st["章节"], 1)
            self.assertEqual(st["回顾草稿"], 1)


if __name__ == "__main__":
    unittest.main()


class TestBibService(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        (self.dir / "src/数学").mkdir(parents=True)
        (self.dir / "src/数学/a.tex").write_text(
            "% ==META== 学科: 数学 | 日期: 2026-08-09\n\\section{x}\n\\cite{keyA}\n% \\cite{commented}\n", encoding="utf-8")
        (self.dir / "refs.bib").write_text("@article{keyA, title={A}}\n@article{unused, title={U}}\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_bib(self):
        bib = BibService(self.dir)
        self.assertEqual(bib.keys(), {"keyA", "unused"})
        self.assertEqual(bib.cited_keys(), {"keyA"})  # 注释的 commented 不算
        self.assertEqual(bib.missing(), [])
        self.assertEqual(bib.unused(), ["unused"])


if __name__ == "__main__":
    unittest.main()


class TestWikiGroup(unittest.TestCase):
    def test_group(self):
        from anote.services.wiki import group_notes
        from anote.services import Note
        notes = [
            Note(Path("/x"), "src/数学/代数/环论.tex", "环论", {"学科": "数学", "分支": "代数"}),
            Note(Path("/x"), "src/数学/代数/群论.tex", "群论", {"学科": "数学", "分支": "代数"}),
            Note(Path("/x"), "src/物理/量子/态.tex", "态", {}),  # 目录推断
        ]
        g = group_notes(notes)
        self.assertEqual(len(g[("数学", "代数")]), 2)
        self.assertEqual(len(g[("物理", "量子")]), 1)


if __name__ == "__main__":
    unittest.main()
