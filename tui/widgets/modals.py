#!/usr/bin/env python3
"""通用弹窗：输入弹窗 + 输出弹窗（各数据页共用）。"""
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


class PromptModal(ModalScreen):
    """输入弹窗：确定/回车后回调 on_submit(value)。"""

    def __init__(self, title, placeholder="", on_submit=None, **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._ph = placeholder
        self._cb = on_submit

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-box"):
            yield Static(f"[b]{self._title}[/b]")
            yield Input(placeholder=self._ph, id="prompt-input")
            yield Button("确定", id="ok")

    def on_mount(self) -> None:
        self.query_one("#prompt-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._finish(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self._finish(self.query_one("#prompt-input", Input).value)

    def _finish(self, value: str) -> None:
        if self._cb:
            self._cb(value)
        self.app.pop_screen()


class OutputModal(ModalScreen):
    """输出弹窗：展示脚本输出/文件内容。"""

    def __init__(self, title, content, **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._content = content

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-box"):
            yield Static(f"[b]{self._title}[/b]")
            yield Static(self._content, id="output")
            yield Button("关闭", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()
