#!/usr/bin/env python3
"""MCP Server 握手/工具测试（stdio 协议，fastmcp 传输）。

不依赖 ~/Projects/Anote 或 ~/Documents/Anote：项目根由测试文件位置推导，
数据目录用 ANOTE_DATA 临时目录隔离；无 fastmcp 时自动跳过。
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER = PROJECT_ROOT / "scripts" / "mcp_server.py"
HAS_FASTMCP = importlib.util.find_spec("fastmcp") is not None


@unittest.skipUnless(HAS_FASTMCP, "fastmcp 未安装（setup.sh --minimal 模式），跳过 MCP 测试")
class TestMcp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = dict(os.environ, ANOTE_DATA=self.tmp.name)
        (Path(self.tmp.name) / "src").mkdir(parents=True, exist_ok=True)
        (Path(self.tmp.name) / "src" / "test.tex").write_text(
            "% ==META== 学科: 测试 | 日期: 2026-08-19\n\\section{x}\n", encoding="utf-8")
        self.proc = subprocess.Popen([sys.executable, str(SERVER)],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1,
                                     env=self.env)

    def tearDown(self):
        for stream in (self.proc.stdin, self.proc.stdout):
            try:
                stream.close()
            except Exception:  # noqa: BLE001
                pass
        self.proc.terminate()
        self.proc.wait(timeout=5)
        self.tmp.cleanup()

    def _send(self, obj):
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def _recv(self):
        return json.loads(self.proc.stdout.readline())

    def _init(self):
        self._send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"}}})
        r = self._recv()
        self.assertEqual(r["result"]["serverInfo"]["name"], "anote")
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def test_handshake_and_tools(self):
        self._init()
        self._send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = [t["name"] for t in self._recv()["result"]["tools"]]
        for expect in ("anote_stats", "anote_search", "anote_ask", "anote_queue", "anote_notes"):
            self.assertIn(expect, tools)

    def test_call_notes(self):
        self._init()
        self._send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                    "params": {"name": "anote_notes", "arguments": {}}})
        text = self._recv()["result"]["content"][0]["text"]
        self.assertIn("src/", text)


if __name__ == "__main__":
    unittest.main()
