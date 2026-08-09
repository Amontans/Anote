#!/usr/bin/env python3
"""全文搜索页：rg 全文检索（结果列表 → 预览/打开）。"""
import subprocess

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static

from tui.widgets.modals import OutputModal


class SearchScreen(Screen):
    BINDINGS = [
        Binding("f2", "open", "打开"),
        Binding("f3", "preview", "预览"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._results = []  # [(path, lineno, snippet)]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("🔍 全文搜索（输入回车检索 · F2 打开 · F3 预览）", classes="screen-title")
        yield Input(placeholder="关键词（如：群论 或 attention）", id="q")
        yield ListView(id="results")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#q", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._search(event.value)

    def _search(self, query: str) -> None:
        lv = self.query_one("#results", ListView)
        lv.clear()
        self._results = self.app.context.rg(query)
        if not self._results:
            lv.append(ListItem(Static("（无结果，换个关键词）")))
            return
        for path, lineno, snippet in self._results:
            rel = path.replace(self.app.context.data_dir + "/", "")
            lv.append(ListItem(Static(f"{rel}:{lineno}  {snippet}")))

    def _selected(self):
        lv = self.query_one("#results", ListView)
        idx = lv.index
        if idx is None or idx >= len(self._results):
            self.notify("先选择一条结果", severity="warning")
            return None
        return self._results[idx]

    def action_open(self) -> None:
        r = self._selected()
        if not r:
            return
        editor = self.app.context.editor
        subprocess.Popen([editor, r[0]], start_new_session=True)
        self.notify(f"已用 {editor} 打开: {r[0]}")

    def action_preview(self) -> None:
        r = self._selected()
        if not r:
            return
        try:
            with open(r[0], encoding="utf-8") as f:
                lines = f.read().splitlines()
            ln = int(r[1])
            lo, hi = max(0, ln - 8), min(len(lines), ln + 8)
            ctx = "\n".join(f"{i+1:4d} | {lines[i]}" for i in range(lo, hi))
        except Exception as e:  # noqa: BLE001
            ctx = f"读取失败: {e}"
        self.app.push_screen(OutputModal(r[0], ctx))
