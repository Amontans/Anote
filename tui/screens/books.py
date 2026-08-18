#!/usr/bin/env python3
"""教科书页：书籍列表 / 章节预览 / 新建书·章 / 编译。"""
import os
import shutil
import subprocess

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

from tui.widgets.modals import OutputModal, PromptModal


class BooksScreen(Screen):
    BINDINGS = [
        Binding("f2", "new_book", "新书"),
        Binding("f3", "new_chapter", "新章"),
        Binding("f4", "build", "编译"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._books = []
        self._selected_book = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("📚 教科书（F2 新书 · F3 新章 · F4 编译）", classes="screen-title")
        yield Horizontal(
            ListView(id="books"),
            Static("← 选择书籍查看章节", id="chapters"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self._reload()

    def _reload(self) -> None:
        lv = self.query_one("#books", ListView)
        lv.clear()
        self._books = []
        base = os.path.join(self.app.context.data_dir, "books")
        if not os.path.isdir(base):
            return
        for d in sorted(os.listdir(base)):
            if d.startswith("_"):
                continue
            self._books.append(d)
            lv.append(ListItem(Static(d)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is None or idx >= len(self._books):
            return
        name = self._books[idx]
        self._selected_book = name
        chapters_dir = os.path.join(self.app.context.data_dir, "books", name, "chapters")
        parts = [f"**{name}**", ""]
        if os.path.isdir(chapters_dir):
            for f in sorted(os.listdir(chapters_dir)):
                if f.endswith(".tex"):
                    parts.append(f"- {f}")
        self.query_one("#chapters", Static).update("\n".join(parts))

    def action_new_book(self) -> None:
        self.app.push_screen(PromptModal("新建教科书", "书名", on_submit=self._new_book))

    def _new_book(self, name: str) -> None:
        if not name.strip():
            return
        data = self.app.context.data_dir
        dst = os.path.join(data, "books", name)
        tpl = os.path.join(data, "books", "_template")
        if os.path.exists(dst):
            self.notify("该书已存在", severity="warning")
            return
        shutil.copytree(tpl, dst)
        main = os.path.join(dst, "main.tex")
        src = open(main, encoding="utf-8").read()
        src = src.replace("书名（在 manage.sh book 生成时填入）", name)
        open(main, "w", encoding="utf-8").write(src)
        self._reload()
        self.notify(f"✓ 教科书 {name} 已创建")

    def action_new_chapter(self) -> None:
        if not self._selected_book:
            self.notify("先选择一本书", severity="warning")
            return
        self.app.push_screen(PromptModal(f"为《{self._selected_book}》添加章节", "章节标题", on_submit=self._new_chapter))

    def _new_chapter(self, title: str) -> None:
        if not title.strip() or not self._selected_book:
            return
        name = self._selected_book
        chapters = os.path.join(self.app.context.data_dir, "books", name, "chapters")
        os.makedirs(chapters, exist_ok=True)
        n = len([f for f in os.listdir(chapters) if f.endswith(".tex")]) + 1
        f = os.path.join(chapters, f"ch{n:02d}.tex")
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(f"% ===== 第 {n} 章 =====\n\\chapter{{{title}}}\n\\label{{ch:auto{n}}}\n\n正文从这里写起。\n")
        self.notify(f"✓ 章节已创建: ch{n:02d}.tex")

    def action_build(self) -> None:
        if not self._selected_book:
            self.notify("先选择书籍", severity="warning")
            return
        name = self._selected_book
        book_dir = os.path.join(self.app.context.data_dir, "books", name)
        self.notify(f"编译《{name}》…")
        r = subprocess.run(["latexmk", "-lualatex", "-interaction=nonstopmode", "main.tex"],
                           cwd=book_dir, capture_output=True, text=True, timeout=300)
        out = (r.stdout + r.stderr)[-3000:] or "（无输出）"
        self.app.push_screen(OutputModal(f"编译《{name}》", out))
