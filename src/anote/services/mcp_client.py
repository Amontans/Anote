"""MCP 客户端服务（v1.12 协议层）：让 Anote 接入任意外部 MCP server。

通过 JSON-RPC over stdio 与外部 MCP server 通信（initialize → tools/list → tools/call）。
外部 server 注册在 ~/.config/anote/external.json：
  {"servers": {"<名>": {"command": ["python3", "-m", "xxx"]}}}
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

CONFIG = Path("~/.config/anote/external.json").expanduser()


def load_servers() -> dict:
    if not CONFIG.exists():
        return {}
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8")).get("servers", {})
    except Exception:  # noqa: BLE001
        return {}


class MCPClient:
    """连接一个外部 MCP server（stdio），列出/调用其工具。"""

    def __init__(self, command: list[str]):
        self.command = command
        self.proc = None
        self._id = 0

    def connect(self) -> None:
        self.proc = subprocess.Popen(
            self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self._send({"jsonrpc": "2.0", "id": self._next(), "method": "initialize", "params": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "anote", "version": "1.0"}}})
        self._recv()
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _next(self) -> int:
        self._id += 1
        return self._id

    def _send(self, obj: dict) -> None:
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def _recv(self) -> dict:
        return json.loads(self.proc.stdout.readline())

    def list_tools(self) -> list[str]:
        self._send({"jsonrpc": "2.0", "id": self._next(), "method": "tools/list"})
        r = self._recv()
        return [t["name"] for t in r.get("result", {}).get("tools", [])]

    def call(self, name: str, args: dict | None = None, timeout: int = 180) -> str:
        self._send({"jsonrpc": "2.0", "id": self._next(), "method": "tools/call",
                    "params": {"name": name, "arguments": args or {}}})
        r = self._recv()
        content = r.get("result", {}).get("content", [])
        return "\n".join(c.get("text", "") for c in content if isinstance(c, dict))

    def close(self) -> None:
        if self.proc:
            self.proc.terminate()
            self.proc = None


def call_server(server_name: str, tool: str, args: dict | None = None) -> str:
    """按注册名调用外部 server 工具。"""
    servers = load_servers()
    if server_name not in servers:
        return f"✗ 未知外部 server: {server_name}（已注册: {list(servers)}）"
    cmd = servers[server_name].get("command", [])
    if not cmd:
        return f"✗ server {server_name} 无 command"
    client = MCPClient(cmd)
    try:
        client.connect()
        return client.call(tool, args)
    finally:
        client.close()
