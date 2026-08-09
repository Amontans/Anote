#!/usr/bin/env python3
"""通用占位页：接口先行——本页未来功能经 app.context 接入，不改文件系统。
填内容时：替换为具体 Screen 并在 anote_app.py 的 SCREENS 注册。
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown


class PlaceholderScreen(Screen):
    def __init__(self, key, title, description, planned, commands=(), **kwargs):
        super().__init__(**kwargs)
        self._key = key
        self._title = title
        self._description = description
        self._planned = planned
        self._commands = commands

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        planned = "\n".join(f"- {p}" for p in self._planned)
        cmds = "\n".join(f"`{c}`" for c in self._commands)
        yield Markdown(f"""# {self._title}（规划中）

{self._description}

## 本页规划
{planned}

## 相关命令
{cmds}

## 实现约定
- 数据读取/写入一律经 `app.context`（AnoteContext 数据总线）
- 命令调用经 `app.context.run_script(...)`（薄壳原则，逻辑留在 scripts/）
- 契约见 `docs/INTERFACES.md` 与 `docs/TUI-PLAN.md`
""")
        yield Footer()

    def on_mount(self) -> None:
        self.title = self._title
