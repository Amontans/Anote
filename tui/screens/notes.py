#!/usr/bin/env python3
"""笔记页：学科树浏览 / 预览 / 新建 / 编辑 / 语义检索。"""
import datetime
import os
import subprocess

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Static, Tree

from tui.widgets.modals import OutputModal, PromptModal


class NotesScreen(Screen):
    BINDINGS = [
        Binding("f2", "new_note", "新建"),
        Binding("f3", "edit", "编辑"),
        Binding("f4", "search", "检索"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selected = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("📝 笔记（F2 新建 · F3 编辑 · F4 语义检索）", classes="screen-title")
        yield Tree("src", id="tree")
        yield Static("← 选择笔记预览", id="preview")
        yield Footer()

    def on_mount(self) -> None:
        self._build_tree()

    def _build_tree(self) -> None:
        tree = self.query_one("#tree", Tree)
        tree.clear()
        root = tree.root
        base = os.path.join(self.app.context.data_dir, "src")
        if not os.path.isdir(base):
            root.add_leaf("（src/ 为空，按 F2 新建第一篇笔记）")
            return
        for disc in sorted(os.listdir(base)):
            dp = os.path.join(base, disc)
            if not os.path.isdir(dp):
                continue
            dnode = root.add(disc, data={"kind": "dir", "path": dp})
            for sub in sorted(os.listdir(dp)):
                sp = os.path.join(dp, sub)
                if os.path.isdir(sp):
                    bnode = dnode.add(sub, data={"kind": "dir", "path": sp})
                    for f in sorted(os.listdir(sp)):
                        if f.endswith((".tex", ".md")) and f != "00-index.tex":
                            bnode.add_leaf(f, data={"kind": "note", "path": os.path.join(sp, f)})
                elif sub.endswith((".tex", ".md")) and sub != "00-index.tex":
                    dnode.add_leaf(sub, data={"kind": "note", "path": sp})
        tree.root.expand()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        d = event.node.data or {}
        if d.get("kind") == "note":
            self._selected = d["path"]
            try:
                with open(d["path"], encoding="utf-8") as f:
                    content = f.read()[:2500]
                self.query_one("#preview", Static).update(content)
            except Exception as e:  # noqa: BLE001
                self.notify(f"读取失败: {e}", severity="error")

    def action_new_note(self) -> None:
        self.app.push_screen(PromptModal("新建笔记", "学科/分支> 标题", on_submit=self._new))

    def _new(self, text: str) -> None:
        if ">" not in text:
            self.notify("格式: 学科/分支> 标题", severity="warning")
            return
        disc, title = text.split(">", 1)
        disc, title = disc.strip(), title.strip()
        if not disc or not title:
            return
        path = os.path.join(self.app.context.data_dir, "src", disc)
        os.makedirs(path, exist_ok=True)
        fname = f"{datetime.date.today().isoformat()}_{title.replace(' ', '_')}.tex"
        rel = os.path.join("src", disc, fname)
        meta = f"% ==META== 学科: {disc.split('/')[0]} | 分支: {disc.split('/')[-1] if '/' in disc else ''} | 标签: | 日期: {datetime.date.today().isoformat()} | 来源: 教材\n"
        body = (f"{meta}\\documentclass[11pt]{{ctexart}}\n\\usepackage[margin=2.5cm]{{geometry}}\n"
                f"\\usepackage{{paralist,amsmath,amssymb}}\n\\title{{{title}}}\n\\date{{\\today}}\n"
                "\\begin{document}\n\\maketitle\n\\section{主题}\n\\begin{compactitem}\n  \\item \n\\end{compactitem}\n\\end{document}\n")
        self.app.context.write_data(rel, body)
        self.app.context.run_script("index-gen.py")
        self._build_tree()
        self.notify(f"✓ 已创建: {rel}")

    def action_edit(self) -> None:
        if not self._selected:
            self.notify("先在树中选择一篇笔记", severity="warning")
            return
        editor = self.app.context.editor
        subprocess.Popen([editor, self._selected], start_new_session=True)
        self.notify(f"已用 {editor} 打开")

    def action_search(self) -> None:
        self.app.push_screen(PromptModal("语义检索", "问题（如：环是什么代数结构）", on_submit=self._search))

    def _search(self, query: str) -> None:
        r = self.app.context.run_script("ask.py", "--semantic", query, timeout=180)
        out = r.stdout or r.stderr or "无结果"
        self.app.push_screen(OutputModal(f"检索: {query}", out[:4000]))
