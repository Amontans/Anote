#!/usr/bin/env python3
"""P2 服务层回归测试：备份/恢复、终端渲染、Web 外壳安全。"""
import os
import shutil
import sys
import tarfile
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.services.backup import create_backup  # noqa: E402
from anote.services.bootstrap import ensure_data_dir  # noqa: E402
from anote.services.mdview import render as render_md  # noqa: E402
from anote.services.restore import extract_archive, restore_backup, verify_checksum  # noqa: E402
from anote.services.webserver import create_handler  # noqa: E402


class TestBackupRestore(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data = Path(self._tmp.name) / "data"
        self.data.mkdir()
        with mock.patch.dict(os.environ, {"ANOTE_DATA": str(self.data)}):
            ensure_data_dir(self.data)
        (self.data / "src" / "a.tex").write_text("% ==META== 学科: 数学 | 日期: 2026-08-19\n", encoding="utf-8")
        (self.data / ".anote" / "logs").mkdir(parents=True, exist_ok=True)
        (self.data / ".anote" / "logs" / "anote.log").write_text("run log", encoding="utf-8")
        (self.data / ".anote" / "external.json").write_text("{}", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_backup_excludes_runtime_and_includes_config(self):
        out = Path(self._tmp.name) / "backups"
        r = create_backup(self.data, out)
        self.assertTrue(r.path.exists())
        with tarfile.open(r.path, "r:gz") as tf:
            names = tf.getnames()
        self.assertTrue(any(n.endswith(".anote/config") for n in names))
        self.assertFalse(any(".anote/logs" in n for n in names))
        ok, _, _ = verify_checksum(r.path)
        self.assertTrue(ok)

    def test_restore_roundtrip(self):
        out = Path(self._tmp.name) / "backups"
        r = create_backup(self.data, out)
        target = Path(self._tmp.name) / "restored"
        report = restore_backup(r.path, target, dry_run=True)
        self.assertTrue(report.ok)
        report = restore_backup(r.path, target, force=True)
        self.assertTrue(report.ok)
        self.assertTrue((target / "src" / "a.tex").exists())
        self.assertTrue((target / ".anote" / "config").exists())

    def test_restore_rejects_path_traversal(self):
        evil = Path(self._tmp.name) / "evil.tar.gz"
        with tarfile.open(evil, "w:gz") as tf:
            import io
            data = b"x"
            info = tarfile.TarInfo("../evil.txt")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        target = Path(self._tmp.name) / "out"
        ok, err = extract_archive(evil, target)
        self.assertFalse(ok)
        self.assertIn("拒绝", err)
        self.assertFalse((Path(self._tmp.name) / "evil.txt").exists())


class TestMdview(unittest.TestCase):
    def test_render_markdown_and_skip_latex(self):
        out = render_md("# 标题\n\n**重点**\n\n% 注释行\n\\section{环}\n正文")
        self.assertIn("标题", out)
        self.assertIn("重点", out)
        self.assertNotIn("注释行", out)
        self.assertNotIn(r"\section", out)


class TestWebServer(unittest.TestCase):
    def test_forbidden_and_index(self):
        with tempfile.TemporaryDirectory() as t:
            data = Path(t)
            (data / ".git").mkdir()
            (data / ".git" / "config").write_text("secret", encoding="utf-8")
            (data / "src").mkdir()
            handler = create_handler(data)
            srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            port = srv.server_address[1]
            th = threading.Thread(target=srv.serve_forever, daemon=True)
            th.start()
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as r:
                    self.assertEqual(r.status, 200)
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(f"http://127.0.0.1:{port}/.git/config", timeout=5)
                self.assertEqual(ctx.exception.code, 404)
            finally:
                srv.shutdown()
                srv.server_close()


if __name__ == "__main__":
    unittest.main()
