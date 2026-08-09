#!/usr/bin/env python3
"""记忆层页：研究日志 / 洞见 / 概念 / 开放问题 四页签 + 追加条目。"""
import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Markdown, Tab, Tabs

from tui.widgets.modals import PromptModal

FILES = [
    ("research-log", "📖 研究日志", "research-log.md"),
    ("insights", "💡 洞见", "insights.md"),
    ("concepts", "🔗 概念", "concepts.md"),
    ("open-questions", "❓ 问题", "open-questions.md"),
]


class MemoryScreen(Screen):
    BINDINGS = [Binding("f2", "append", "追加条目")]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("🧠 记忆层（F2 追加条目）", classes="screen-title")
        yield Tabs(*[Tab(name, id=key) for key, name, _ in FILES], id="tabs")
        yield Markdown("", id="md")
        yield Footer()

    def on_mount(self) -> None:
        self._load(0)

    def _load(self, idx: int) -> None:
        self._current = idx
        rel = "memory/" + FILES[idx][2]
        try:
            content = self.app.context.read_data(rel)
        except Exception:  # noqa: BLE001
            content = f"（{rel} 不存在）"
        self.query_one("#md", Markdown).update(content)

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        for i, (key, _, _) in enumerate(FILES):
            if key == event.tab.id:
                self._load(i)
                return

    def action_append(self) -> None:
        name = FILES[self._current][1]
        self.app.push_screen(PromptModal(f"追加到 {name}", "内容", on_submit=self._append))

    def _append(self, text: str) -> None:
        if not text.strip():
            return
        rel = "memory/" + FILES[self._current][2]
        try:
            content = self.app.context.read_data(rel)
        except Exception:  # noqa: BLE001
            content = f"# {FILES[self._current][1]}\n"
        if self._current == 0:  # research-log: 带日期标题
            entry = f"\n## {datetime.date.today().isoformat()}\n- {text.strip()}\n"
        else:
            entry = f"- {text.strip()}\n"
        self.app.context.write_data(rel, content.rstrip() + "\n" + entry)
        self._load(self._current)
        self.notify("✓ 已追加")
