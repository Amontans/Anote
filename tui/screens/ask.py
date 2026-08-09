#!/usr/bin/env python3
"""AI 问答页：经 Pi（agent）回答——Pi 自动加载 Anote 协议/规则/记忆，并可用 anote 检索笔记。

流程：输入问题 → 后台调 pi -p → Markdown 渲染回答；回答会引用知识库（Pi 按协议执行）。
"""
import time

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, Markdown, Static


class AskScreen(Screen):
    BINDINGS = [Binding("f2", "clear", "清空")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("🤖 AI 问答（经 Pi · 自动加载 Anote 协议，可检索知识库）", classes="screen-title")
        yield Input(placeholder="输入问题，回车提问（如：根据我的笔记，环和群有什么关系？）", id="question")
        yield Static("", id="status")
        yield Markdown("", id="answer")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#question", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._ask(event.value)

    def _ask(self, question: str) -> None:
        if not question.strip():
            return
        self.query_one("#status", Static).update("⏳ Pi 思考中…（可检索你的知识库）")
        self.query_one("#answer", Markdown).update("")
        self.app.run_worker(self._ask_async(question.strip()))

    async def _ask_async(self, question: str) -> None:
        t0 = time.time()
        r = await self.app.context.run_pi_async(question)
        dt = time.time() - t0
        if r.ok:
            self.query_one("#status", Static).update(f"✅ 完成（{dt:.0f}s · 经 Pi → DeepSeek）")
            self.query_one("#answer", Markdown).update(r.stdout or "（Pi 无输出）")
        else:
            self.query_one("#status", Static).update(f"❌ 失败（{dt:.0f}s）: {r.stderr or '未知错误'}")

    def action_clear(self) -> None:
        self.query_one("#question", Input).value = ""
        self.query_one("#status", Static).update("")
        self.query_one("#answer", Markdown).update("")
        self.query_one("#question", Input).focus()
