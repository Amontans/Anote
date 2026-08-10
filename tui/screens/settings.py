#!/usr/bin/env python3
"""设置页：数据目录（可改，P3 接迁移向导）/ 编辑器（可选）/ 语言。"""
import os

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static

from tui.context import ConfigChanged
from tui.widgets.modals import OutputModal, PromptModal

EDITOR_CHOICES = ["code", "vim", "nvim", "emacs", "gedit", "nano"]
THEMES = ["textual-dark", "textual-light", "nord", "gruvbox", "monokai", "tokyo-night"]


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
        yield Label("TUI 主题")
        yield Select([(t, t) for t in THEMES], id="theme")
        yield Horizontal(
            Button("保存 (F2)", id="save"),
            Button("迁移数据位置…", id="migrate"),
        )
        yield Footer()

    def on_mount(self) -> None:
        ctx = self.app.context
        self.query_one("#data_dir", Input).value = ctx.data_dir
        self.query_one("#editor", Select).value = ctx.editor
        self.query_one("#lang", Select).value = ctx.lang
        try:
            self.query_one("#theme", Select).value = ctx.config.get("theme", "textual-dark")
        except Exception:  # noqa: BLE001
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.action_save()
        elif event.button.id == "migrate":
            self.app.push_screen(PromptModal("迁移数据目录", "新路径（如 ~/Documents/Anote2）", on_submit=self._migrate))

    def _migrate(self, target: str) -> None:
        if not target.strip():
            return
        self.app.run_worker(self._migrate_async(target.strip()))

    async def _migrate_async(self, target: str) -> None:
        self.notify(f"迁移中：{target} …（含 .git 历史，请稍候）")
        r = await self.app.context.run_script_async("migrate.py", "--to", target, "--force", "--with-env")
        self.app.push_screen(OutputModal("迁移结果", (r.stdout or "") + (r.stderr or "")))
        self.app.post_message(ConfigChanged())

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
        try:
            th = self.query_one("#theme", Select).value
            if th:
                ctx.set_config("theme", str(th))
                self.app.theme = str(th)
        except Exception:  # noqa: BLE001
            pass
        self.app.post_message(ConfigChanged())
        self.notify("设置已保存")
