#!/usr/bin/env python3
"""队列页：queue.md 表格 / 状态切换（📥→📖→✅→🗄）/ 检索入队 / 打开笔记。"""
import re
import subprocess

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Label

from tui.widgets.modals import OutputModal, PromptModal

STATUSES = ["📥", "📖", "✅", "🗄"]
META = "<!-- 活动队列 -->"


class QueueScreen(Screen):
    BINDINGS = [
        Binding("space", "cycle", "切换状态"),
        Binding("f2", "add", "检索入队"),
        Binding("f3", "open", "打开笔记"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._rows = []  # [(原始行, 状态, 日期, 论文, id, 笔记)]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("📥 文献队列（空格=切换状态 · F2 检索入队 · F3 打开笔记）", classes="screen-title")
        yield DataTable(id="queue")
        yield Footer()

    def on_mount(self) -> None:
        self._reload()

    def _reload(self) -> None:
        table = self.query_one("#queue", DataTable)
        table.clear(columns=True)
        table.add_columns("状态", "日期", "论文", "ID", "笔记")
        self._rows = []
        try:
            text = self.app.context.read_data("queue.md")
        except Exception:  # noqa: BLE001
            self.notify("queue.md 读取失败", severity="error")
            return
        for line in text.splitlines():
            m = re.match(r"^\|\s*(📥|📖|✅|🗄)\s*\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\s*\|", line)
            if m:
                row = (line, m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip(), m.group(5).strip())
                self._rows.append(row)
                table.add_row(m.group(1), row[2], row[3], row[4], row[5])
        if not self._rows:
            table.add_row("—", "—", "（队列为空：F2 检索文献入队）", "—", "—")

    def action_cycle(self) -> None:
        table = self.query_one("#queue", DataTable)
        idx = table.cursor_row
        if idx is None or idx >= len(self._rows):
            self.notify("先选择一行", severity="warning")
            return
        line, status, *_ = self._rows[idx]
        nxt = STATUSES[(STATUSES.index(status) + 1) % len(STATUSES)]
        new_line = line.replace(f"| {status} |", f"| {nxt} |", 1)
        self._rewrite_line(line, new_line)
        self.notify(f"状态: {status} → {nxt}")

    def _rewrite_line(self, old_line, new_line) -> None:
        try:
            text = self.app.context.read_data("queue.md")
        except Exception:  # noqa: BLE001
            return
        text = text.replace(old_line, new_line, 1)
        self.app.context.write_data("queue.md", text)
        self._reload()

    def action_add(self) -> None:
        self.app.push_screen(PromptModal("文献检索入队", "关键词（arXiv）", on_submit=self._add))

    def _add(self, query: str) -> None:
        r = self.app.context.run_script(
            "search.py", "--provider", "arxiv", "--query", query,
            "--max", "10", "--queue", self.app.context.data_dir + "/queue.md", timeout=180)
        self._reload()
        self.app.push_screen(OutputModal(f"检索: {query}", (r.stdout or r.stderr or "")[:4000]))

    def action_open(self) -> None:
        table = self.query_one("#queue", DataTable)
        idx = table.cursor_row
        if idx is None or idx >= len(self._rows):
            self.notify("先选择一行", severity="warning")
            return
        note_rel = self._rows[idx][5]
        if note_rel and note_rel != "—" and not note_rel.startswith("src/"):
            note_rel = f"src/papers/{note_rel}"
        if not note_rel or note_rel == "—":
            self.notify("该条目无笔记链接", severity="warning")
            return
        try:
            content = self.app.context.read_data(note_rel)
            self.app.push_screen(OutputModal(note_rel, content[:4000]))
        except Exception:  # noqa: BLE001
            self.notify(f"笔记不存在: {note_rel}", severity="error")
