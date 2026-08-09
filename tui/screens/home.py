#!/usr/bin/env python3
"""主页仪表盘：状态总览 + 快速动作。"""
import os

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Markdown, Static


class HomeScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown("# Anote 科研知识库\n\n按 `?` 帮助 · `/` 命令面板 · `F5` 自检 · `s` 设置")
        yield Static(id="stats")
        yield Horizontal(
            Button("📝 笔记", id="btn-notes"),
            Button("📥 队列", id="btn-queue"),
            Button("✅ 自检", id="btn-check"),
            Button("⚙️ 设置", id="btn-settings"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_stats()

    def refresh_stats(self):
        ctx = self.app.context
        counts = ctx.queue_counts()
        sem = "✓" if ctx.semantic_ready() else "✗（notes index-semantic）"
        self.query_one("#stats", Static).update(
            f"**数据目录** `{ctx.data_dir}`  |  **笔记** {ctx.note_count()} 篇\n\n"
            f"**队列** 📥{counts['📥']} 📖{counts['📖']} ✅{counts['✅']} 🗄{counts['🗄']}  |  "
            f"**语义索引** {sem}  |  **最近回顾** {ctx.last_review()}\n\n"
            f"**编辑器** {ctx.editor}（可在设置中更改）"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        b = event.button.id
        if b == "btn-notes":
            self.app.action_go_notes()
        elif b == "btn-queue":
            self.app.action_go_queue()
        elif b == "btn-check":
            self.app.action_check()
        elif b == "btn-settings":
            self.app.action_go_settings()
