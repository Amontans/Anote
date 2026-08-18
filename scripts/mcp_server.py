#!/usr/bin/env python3
"""Anote MCP Server：把 Anote 能力暴露给任何 MCP 客户端（Pi/Claude/其他 AI 工具）。

接口声明（契约）:
    输入: MCP JSON-RPC over stdio（initialize → tools/list → tools/call）
    输出: MCP 协议响应（stdio）；退出码 0
    副作用: 工具调用可能写数据（anote_search 只读；后续工具按需）
用法: anote mcp   （或直接运行本脚本）
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import BibService, NotesService, QueueService, StatsService  # noqa: E402

from fastmcp import FastMCP  # noqa: E402

mcp = FastMCP("anote")

DATA = Config.load().data_dir


def _run(script: str, *args: str, timeout: int = 120) -> str:
    """调用 anote 脚本（薄适配器），返回 stdout 或错误。"""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)
    env = dict(os.environ, ANOTE_DATA=str(DATA))
    try:
        r = subprocess.run([sys.executable, p, *args], capture_output=True,
                           text=True, timeout=timeout, env=env)
        return r.stdout or (f"✗ {r.stderr}" if r.stderr else "")
    except Exception as e:  # noqa: BLE001
        return f"✗ {e}"


@mcp.tool()
def anote_stats() -> str:
    """Anote 数据统计（笔记/论文/书/队列等各类文件数）。"""
    return json.dumps(StatsService(DATA).compute(), ensure_ascii=False, indent=2)


@mcp.tool()
def anote_search(query: str, max_results: int = 20) -> str:
    """在 Anote 知识库全文检索（rg），返回 文件:行号:片段。"""
    env = dict(os.environ, ANOTE_DATA=str(DATA))
    cmd = ["rg", "-n", "-i", query, str(DATA),
           "-g", "*.tex", "-g", "*.md", "-g", "!00-index.tex", "-g", "!README.md"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
    except FileNotFoundError:
        return "✗ 未找到 rg"
    lines = [l for l in r.stdout.splitlines() if l.strip()][:max_results]
    return "\n".join(lines) or "（无结果）"


@mcp.tool()
def anote_ask(query: str) -> str:
    """语义问答（bge 向量检索 top-k，省 token 只返回相关片段）。"""
    return _run("ask.py", "--semantic", query, timeout=180)


@mcp.tool()
def anote_queue() -> str:
    """论文待读队列（📥待读 📖在读 ✅精读 🗄归档）。"""
    q = QueueService(DATA)
    return "\n".join(f"{e.status} {e.date} {e.title} | {e.key}" for e in q.read_entries())


@mcp.tool()
def anote_notes(filter: str = "") -> str:
    """列出笔记（可按 学科/标签/文件名 过滤）。"""
    svc = NotesService(DATA)
    notes = svc.filter(filter) if filter else svc.scan()
    return "\n".join(f"{n.rel}  [{', '.join(n.meta.values())}]" for n in notes[:100])



@mcp.tool()
def anote_bib() -> str:
    """引用库状态：refs.bib 条目数 + 缺失引用键 + 冗余条目。"""
    bib = BibService(DATA)
    return json.dumps({
        "entries": len(bib.keys()),
        "cited": len(bib.cited_keys()),
        "missing": bib.missing(),
        "unused": bib.unused()[:20],
    }, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)  # 不联网检查新版本，离线可用

