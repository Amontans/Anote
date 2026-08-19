#!/usr/bin/env python3
"""Anote 核心/服务单元测试（stdlib unittest，临时目录隔离，ANOTE_DATA env）。"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config, Result, config_path_for  # noqa: E402
from anote.services import BibService, NotesService, QueueService, StatsService  # noqa: E402


class TestConfig(unittest.TestCase):
    def test_env_override(self):
        with tempfile.TemporaryDirectory() as t:
            with patch.dict(os.environ, {"ANOTE_DATA": t}):
                cfg = Config.load()
                self.assertEqual(cfg.data_dir, Path(t))
                self.assertEqual(config_path_for(cfg.data_dir), Path(t) / ".anote" / "config")

    def test_save_set_and_reader(self):
        with tempfile.TemporaryDirectory() as t:
            with patch.dict(os.environ, {"ANOTE_DATA": t}):
                cfg = Config.load()
                cfg.set("editor", "vim")
                cfg.set("reader", "zathura")
                self.assertEqual(Config.load().editor, "vim")
                self.assertEqual(Config.load().reader, "zathura")
                self.assertTrue((Path(t) / ".anote" / "config").exists())

    def test_data_dir_cannot_be_set_directly(self):
        with tempfile.TemporaryDirectory() as t:
            with patch.dict(os.environ, {"ANOTE_DATA": t}):
                with self.assertRaises(ValueError):
                    Config().set("data_dir", "/tmp/elsewhere")

    def test_pointer_resolution_and_update(self):
        """定位指针决定非默认数据根；保存配置后指针同步更新。"""
        from anote.core import LEGACY_CONFIG_PATH, config_path_for
        with tempfile.TemporaryDirectory() as t:
            home = Path(t)
            data = home / "data"
            data.mkdir()
            pointer = home / ".config" / "anote" / "config"
            pointer.parent.mkdir(parents=True)
            pointer.write_text(f"data_dir={data}\n", encoding="utf-8")
            with patch("anote.core.LEGACY_CONFIG_PATH", pointer), \
                    patch.dict(os.environ, {"ANOTE_DATA": ""}):
                cfg = Config.load()
                self.assertEqual(cfg.data_dir, data)
                cfg.set("editor", "emacs")
                # 完整配置在数据根，指针文件只剩 data_dir
                self.assertEqual(config_path_for(data).read_text(encoding="utf-8").splitlines()[0],
                                 f"data_dir={data}")
                self.assertEqual(pointer.read_text(encoding="utf-8").strip(),
                                 f"data_dir={data}")

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

    def test_create_does_not_overwrite_and_escapes(self):
        with patch.dict(os.environ, {"ANOTE_DATA": str(self.dir)}):
            s = NotesService(self.dir)
            p = s.create("物理/量子", "A & B")
            self.assertTrue(p.exists())
            self.assertIn(r"\&", p.read_text(encoding="utf-8"))
            with self.assertRaises(FileExistsError):
                s.create("物理/量子", "A & B")


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


class TestBibService(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        (self.dir / "src/数学").mkdir(parents=True)
        (self.dir / "src/数学/a.tex").write_text(
            "% ==META== 学科: 数学 | 日期: 2026-08-09\n\\section{x}\n\\cite{keyA}\n% \\cite{commented}\n",
            encoding="utf-8")
        (self.dir / "refs.bib").write_text(
            "@article{keyA, title={A}}\n@article{unused, title={U}}\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_bib(self):
        bib = BibService(self.dir)
        self.assertEqual(bib.keys(), {"keyA", "unused"})
        self.assertEqual(bib.cited_keys(), {"keyA"})
        self.assertEqual(bib.missing(), [])
        self.assertEqual(bib.unused(), ["unused"])


class TestPaper(unittest.TestCase):
    def test_collect_materials_bm25(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "src/数学/代数").mkdir(parents=True)
            (d / "src/数学/代数/环论.tex").write_text(
                "% ==META== 学科: 数学 | 分支: 代数 | 标签: 环 | 日期: 2026-08-10\n"
                "\\section{环}\n环是带有两个二元运算的集合。\n", encoding="utf-8")
            (d / ".semantic").mkdir()
            (d / ".semantic/chunks.json").write_text(json.dumps({
                "schema_version": 1,
                "chunks": [{"path": str(d / "src/数学/代数/环论.tex"), "mtime": 1,
                            "text": "环 环是带有两个二元运算的集合 交换群 分配律"}]}),
                encoding="utf-8")
            from anote.services.paper import collect_materials
            m = collect_materials("环", d, top=3)
            self.assertTrue(any("环论.tex" in n for n in m["notes"]))


class TestWikiGroup(unittest.TestCase):
    def test_group(self):
        from anote.services.wiki import group_notes
        from anote.services import Note
        notes = [
            Note(Path("/x"), "src/数学/代数/环论.tex", "环论", {"学科": "数学", "分支": "代数"}),
            Note(Path("/x"), "src/数学/代数/群论.tex", "群论", {"学科": "数学", "分支": "代数"}),
            Note(Path("/x"), "src/物理/量子/态.tex", "态", {}),
        ]
        g = group_notes(notes)
        self.assertEqual(len(g[("数学", "代数")]), 2)
        self.assertEqual(len(g[("物理", "量子")]), 1)


class TestRetrieval(unittest.TestCase):
    def test_bm25_ranks(self):
        from anote.services.retrieval import BM25Index, tokenize
        chunks = [
            {"text": "环是带有两个二元运算的集合，加法构成交换群"},
            {"text": "群是集合配合二元运算，满足封闭性结合律单位元逆元"},
            {"text": "Transformer 用自注意力代替循环结构"},
        ]
        idx = BM25Index(chunks)
        scores = idx.score("环 二元运算")
        self.assertEqual(max(range(3), key=lambda i: scores[i]), 0)
        self.assertEqual(tokenize("环论"), ["环论"])

    def test_bm25_save_load(self):
        from anote.services.retrieval import BM25Index
        with tempfile.TemporaryDirectory() as t:
            chunks = [{"text": "环 群 二元运算"}, {"text": "注意力机制 transformer"}]
            idx = BM25Index(chunks)
            cache = Path(t) / "bm25.json"
            sig = "abc"
            idx.save(cache, sig)
            loaded = BM25Index.load(cache, sig)
            self.assertEqual(loaded.n, 2)
            self.assertEqual(loaded.score("环"), idx.score("环"))
            with self.assertRaises(ValueError):
                BM25Index.load(cache, "wrong")

    def test_tokenize(self):
        from anote.services.retrieval import tokenize
        self.assertIn("attention", tokenize("Attention is all you need"))
        self.assertTrue(any("环" in t for t in tokenize("环论基础")))


class TestEbook(unittest.TestCase):
    def test_extract_epub(self):
        import io
        import zipfile as zf
        from anote.services.ebooks import extract_epub
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "test.epub"
            with zf.ZipFile(p, "w") as z:
                z.writestr("content/ch1.xhtml",
                           "<html><body><h1>第一章</h1><p>环论基础内容。</p></body></html>")
            text = extract_epub(p)
            self.assertIn("第一章", text)
            self.assertIn("环论", text)


class TestDocs(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        (self.dir / "pdfs").mkdir()
        (self.dir / "pdfs/测试.pdf").write_bytes(b"%PDF-1.4 test" + b"\x00" * 100)

    def tearDown(self):
        self._tmp.cleanup()

    def test_add_dedup_update_stats(self):
        from anote.services.docs import DocService
        svc = DocService(self.dir)
        ok, _ = svc.add("pdfs/测试.pdf")
        self.assertTrue(ok)
        ok2, msg = svc.add("pdfs/测试.pdf")
        self.assertFalse(ok2)
        svc.mark_read("pdfs/测试.pdf")
        svc.progress("pdfs/测试.pdf", "50%")
        e = svc.find("pdfs/测试.pdf")
        self.assertEqual(e.status, "📖")
        self.assertEqual(e.progress, "50%")
        st = svc.stats()
        self.assertEqual(st["total"], 1)
        self.assertEqual(st["status"]["📖"], 1)


class TestMigrationFinalize(unittest.TestCase):
    def test_finalize_config_updates_pointer(self):
        from anote.core import LEGACY_CONFIG_PATH, config_path_for
        from anote.services.migration import finalize_config
        with tempfile.TemporaryDirectory() as t:
            home = Path(t)
            src = home / "src"
            dst = home / "dst"
            src.mkdir()
            pointer = home / ".config" / "anote" / "config"
            pointer.parent.mkdir(parents=True)
            pointer.write_text(f"data_dir={src}\n", encoding="utf-8")
            with patch("anote.core.LEGACY_CONFIG_PATH", pointer), \
                    patch.dict(os.environ, {"ANOTE_DATA": str(src)}):
                finalize_config(dst)
                self.assertEqual(pointer.read_text(encoding="utf-8").strip(), f"data_dir={dst}")
                self.assertTrue(config_path_for(dst).exists())


class TestBootstrap(unittest.TestCase):
    def test_ensure_data_dir(self):
        from anote.services.bootstrap import ensure_data_dir
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            with patch.dict(os.environ, {"ANOTE_DATA": str(d)}):
                r1 = ensure_data_dir(d)
                self.assertGreater(r1["created_files"], 0)
                self.assertTrue((d / ".anote" / "config").exists())
                r2 = ensure_data_dir(d)
                self.assertEqual(r2["created_files"], 0)


if __name__ == "__main__":
    unittest.main()
