#!/usr/bin/env python3
"""MCP Server 握手/工具测试（stdio 协议，fastmcp 传输）。"""
import json
import os
import subprocess
import sys
import unittest

VENV_PY = os.path.expanduser("~/Documents/Anote/.venv/bin/python")
SERVER = os.path.expanduser("~/Projects/Anote/scripts/mcp_server.py")


class TestMcp(unittest.TestCase):
    def setUp(self):
        self.proc = subprocess.Popen([VENV_PY, SERVER],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def tearDown(self):
        self.proc.terminate()

    def _send(self, obj):
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def _recv(self):
        return json.loads(self.proc.stdout.readline())

    def test_handshake_and_tools(self):
        self._send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"}}})
        r = self._recv()
        self.assertEqual(r["result"]["serverInfo"]["name"], "anote")
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self._send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = [t["name"] for t in self._recv()["result"]["tools"]]
        for expect in ("anote_stats", "anote_search", "anote_ask", "anote_queue", "anote_notes"):
            self.assertIn(expect, tools)

    def test_call_notes(self):
        self._send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"}}})
        self._recv()
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self._send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                    "params": {"name": "anote_notes", "arguments": {}}})
        text = self._recv()["result"]["content"][0]["text"]
        self.assertIn("src/", text)


if __name__ == "__main__":
    unittest.main()
