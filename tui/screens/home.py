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
        st = ctx.stats()
        sem = "✓" if ctx.semantic_ready() else "✗（anote index-semantic）"
        n = st.get("笔记总数", ctx.note_count())
        b = st.get("教科书", 0)
        ch = st.get("章节", 0)
        p = st.get("论文精读", 0)
        rv = st.get("回顾草稿", 0)
        self.query_one("#stats", Static).update(
            f"**数据目录** `{ctx.data_dir}`\n\n"
            f"📝 笔记 **{n}** · 📄 论文 **{p}** · 📚 书 **{b}**（章 {ch}）· 🔄 回顾 **{rv}**\n"
            f"📥 队列 📥{counts['📥']} 📖{counts['📖']} ✅{counts['✅']} 🗄{counts['🗄']}\n\n"
            f"语义索引 {sem} · 最近回顾 {ctx.last_review()} · 编辑器 {ctx.editor}"
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
