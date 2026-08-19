#!/usr/bin/env python3
"""命令元数据（单一表）：消费 src/anote/commands.py 注册表。

帮助页 + 命令面板共用，避免双份维护。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from textual.command import Hit, Provider  # noqa: E402

from anote.commands import COMMAND_META  # noqa: E402

# 面板中只暴露高频命令，完整清单见 anote help
PANEL_KEYS = ("index", "index-semantic", "check", "review", "ask", "new",
              "book", "book-build", "chapter", "project", "commit", "backup", "tui")


def panel_commands():
    return [m for m in COMMAND_META if m.name in PANEL_KEYS]


BINDINGS_HELP = [
    ("F1", "帮助"),
    ("Ctrl+F", "全文搜索"),
    ("Ctrl+A", "AI 问答（经 Pi）"),
    ("Ctrl+H / N / Q / M / B / R", "主页 / 笔记 / 队列 / 记忆 / 书 / 回顾"),
    ("Ctrl+S", "设置"),
    ("F5", "运行自检"),
    ("Ctrl+D", "退出"),
    ("（输入框内直接打字，不影响导航）", ""),
]


class AnoteCommands(Provider):
    """命令面板：模糊搜索 Anote 高频命令。"""

    async def discover(self):
        for meta in panel_commands():
            yield Hit(display=meta.name, command=meta.syntax, help=meta.help)

    async def search(self, query):
        q = query.lower()
        for meta in panel_commands():
            if q in meta.name.lower() or q in meta.help.lower():
                yield Hit(display=meta.name, command=meta.syntax, help=meta.help)
