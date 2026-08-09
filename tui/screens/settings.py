#!/usr/bin/env python3
"""设置页：数据目录（可改，P3 接迁移向导）/ 编辑器（可选）/ 语言。"""
import os

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static

from tui.context import ConfigChanged

EDITOR_CHOICES = ["code", "vim", "nvim", "emacs", "gedit", "nano"]


class SettingsScreen(Screen):
    BINDINGS = [("f2", "save", "保存")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("# 设置", classes="title")
        yield Label("数据目录（修改路径后，P3 向导将自动迁移数据，含 .git 历史）")
        yield Input(placeholder="~/Documents/Anote", id="data_dir")
        yield Label("编辑器（打开笔记/教科书用）")
        yield Select([(e, e) for e in EDITOR_CHOICES], id="editor")
        yield Label("界面语言")
        yield Select([("中文", "zh"), ("English", "en")], id="lang")
        yield Horizontal(
            Button("保存 (F2)", id="save"),
            Button("迁移数据位置…（P3）", id="migrate", disabled=True),
        )
        yield Footer()

    def on_mount(self) -> None:
        ctx = self.app.context
        self.query_one("#data_dir", Input).value = ctx.data_dir
        self.query_one("#editor", Select).value = ctx.editor
        self.query_one("#lang", Select).value = ctx.lang

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.action_save()
        elif event.button.id == "migrate":
            self.notify("迁移向导将在 P3 实现（rsync + .git 一起搬 + 校验回滚）")

    def action_save(self) -> None:
        ctx = self.app.context
        dd = self.query_one("#data_dir", Input).value.strip()
        if dd:
            ctx.set_config("data_dir", os.path.expanduser(dd))
        ed = self.query_one("#editor", Select).value
        if ed:
            ctx.set_config("editor", str(ed))
        lang = self.query_one("#lang", Select).value
        if lang:
            ctx.set_config("lang", str(lang))
        self.app.post_message(ConfigChanged())
        self.notify("设置已保存")
