#!/usr/bin/env python3
"""帮助页：快捷键 + 命令手册（数据来自命令注册表）+ 学习路径。"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown

from anote.commands import COMMAND_META
from tui.commands import BINDINGS_HELP


class HelpScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        binds = "\n".join(f"- `{k}` {d}" for k, d in BINDINGS_HELP)
        rows = "\n".join(f"| `{m.syntax}` | {m.help} |" for m in COMMAND_META)
        yield Markdown(f"""# Anote 帮助

## 快捷键
{binds}

## 命令手册
| 命令 | 说明 |
|------|------|
{rows}

## 2 分钟上手
1. `anote new 数学/代数 "标题"` — 建第一篇笔记（自动 META 模板）
2. `anote ask --semantic "问题"` — 对知识库提问
3. `anote review` — 周回顾（AI 提炼，你确认）
4. `anote book "书名"` — 开写教科书

## 更多
- 完整文档：项目目录 `README.md` 与 `docs/USER-GUIDE.md`
- 接口契约：`docs/INTERFACES.md`
- 忘记细节？直接问 Pi——它已读 Anote 协议
""")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "帮助"
