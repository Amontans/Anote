#!/usr/bin/env python3
"""新手引导页（Onboarding）：首次运行 3 步走完上手。"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Markdown

WELCOME = """# 欢迎使用 Anote 🎓

你的科研知识库系统——**纯 TEX 资产 + AI 辅助 + 可迁移**。

## 三分钟上手

### ① 记笔记
在任意终端：`anote new 数学/代数 "标题"` 创建笔记（自动带 META），
用 VS Code/Vim 书写；或在本 TUI 按 `Ctrl+N` 到笔记页按 `F2`。

### ② 提问
- 终端：`anote ask --semantic "环是什么代数结构"`
- 本 TUI：笔记页按 `F4` 语义检索
- 或直接问你的 Pi——它已读 Anote 操作协议

### ③ 沉淀
每周 `anote review` 让 AI 提炼洞见/概念；`anote book "书名"` 把知识写成教科书。

## 关键概念
- **`src/`** = 你的笔记（唯一真相源，纯 TEX）
- **`memory/`** = AI 维护的记忆层（日志/洞见/概念/问题）
- **数据目录可迁移**：设置页改路径，自动搬走（含 git 历史）
- 所有数据纯文本，任何工具倒闭都不影响你的知识

> 按 `F1` 随时看帮助，`Ctrl+P` 命令面板。
"""


class OnboardingScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown(WELCOME)
        yield Button("开始使用", id="start", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.context.set_config("onboarded", "true")
        self.app.switch_screen("home")
