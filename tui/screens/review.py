#!/usr/bin/env python3
"""回顾页：回顾草稿列表 / 预览 / 一键生成。"""
import os

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView, Markdown, Static

from tui.widgets.modals import OutputModal


class ReviewScreen(Screen):
    BINDINGS = [Binding("f2", "generate", "生成回顾")]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._drafts = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("🔄 回顾（F2 生成周回顾草稿）", classes="screen-title")
        yield Horizontal(
            ListView(id="drafts"),
            Markdown("← 选择草稿预览", id="preview"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self._reload()

    def _reload(self) -> None:
        lv = self.query_one("#drafts", ListView)
        lv.clear()
        self._drafts = []
        d = os.path.join(self.app.context.data_dir, "memory", "reviews")
        if not os.path.isdir(d):
            return
        for f in sorted(os.listdir(d), reverse=True):
            if f.endswith(".md"):
                self._drafts.append(f)
                lv.append(ListItem(Static(f)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is None or idx >= len(self._drafts):
            return
        try:
            content = self.app.context.read_data("memory/reviews/" + self._drafts[idx])
        except Exception:  # noqa: BLE001
            content = "（读取失败）"
        self.query_one("#preview", Markdown).update(content)

    def action_generate(self) -> None:
        r = self.app.context.run_script("review.py", "--days", "7", timeout=60)
        self._reload()
        self.notify("回顾草稿已生成（AI 会在后续会话中提炼确认）")
