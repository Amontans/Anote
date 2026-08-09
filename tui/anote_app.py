#!/usr/bin/env python3
"""Anote TUI 主应用：屏幕注册表 + 全局键位 + 命令面板 + 配置事件流。

接口约定（后续部件遵守）：
- 新增屏幕：写入 SCREENS 注册 + 全局键位 BINDINGS + 对应 action
- 部件数据访问：一律经 self.app.context（AnoteContext 数据总线）
- 命令执行：self.app.context.run_script(...)（薄壳原则）
- 设置变更：SettingsScreen 发 ConfigChanged → 本应用转发刷新
"""
from textual.app import App, ComposeResult
from textual.binding import Binding

from tui.commands import AnoteCommands
from tui.context import AnoteContext, ConfigChanged
from tui.screens.help import HelpScreen
from tui.screens.home import HomeScreen
from tui.screens.placeholders import PlaceholderScreen
from tui.screens.settings import SettingsScreen

PLACEHOLDERS = {
    "notes": ("📝 笔记", "浏览学科树、预览、新建、编辑、语义检索笔记。",
              ["学科树浏览（目录 + META 预览）", "新建笔记（调 notes new）", "编辑（$editor 打开）",
               "语义检索（调 ask.py --semantic，结果面板）"]),
    "queue": ("📥 文献队列", "论文生命周期：待读 → 在读 → 已精读 → 归档。",
              ["队列表格渲染（queue.md）", "状态切换（📥→📖→✅→🗄）",
               "文献检索入队（调 search.py --queue）", "跳转精读笔记"]),
    "memory": ("🧠 记忆层", "研究日志 / 洞见 / 概念 / 开放问题 四页签。",
               ["四文件页签查看/追加", "运行回顾（调 review.py）", "查看回顾草稿"]),
    "books": ("📚 教科书", "ctexbook 书籍与章节管理。",
              ["书/章节列表", "新建书/章（调 notes book/chapter）", "编译输出面板（book-build）"]),
    "review": ("🔄 回顾", "周期性知识编译：散点笔记 → 结构化知识。",
               ["最近回顾草稿列表", "一键生成回顾（调 review.py）", "提炼结果确认流"]),
}


class AnoteApp(App):
    TITLE = "Anote · 科研知识库"
    SUB_TITLE = "v0.8.0-dev"
    CSS = """
    Screen { background: #1e1e2e; }
    #stats { padding: 1 2; border: round #585b70; margin: 1 0; }
    Button { margin: 0 1 0 0; }
    Label { margin-top: 1; }
    Input, Select { margin-bottom: 1; }
    """
    BINDINGS = [
        Binding("f1", "go_help", "帮助", priority=True),
        Binding("ctrl+h", "go_home", "主页", priority=True),
        Binding("ctrl+n", "go_notes", "笔记", priority=True),
        Binding("ctrl+q", "go_queue", "队列", priority=True),
        Binding("ctrl+m", "go_memory", "记忆", priority=True),
        Binding("ctrl+b", "go_books", "书", priority=True),
        Binding("ctrl+r", "go_review", "回顾", priority=True),
        Binding("ctrl+s", "go_settings", "设置", priority=True),
        Binding("f5", "check", "自检", priority=True),
        Binding("ctrl+d", "quit", "退出", priority=True),
        Binding("ctrl+p", "command_palette", "命令面板", priority=True),
    ]
    COMMANDS = [AnoteCommands]
    SCREENS = {
        "home": HomeScreen,
        "settings": SettingsScreen,
        "help": HelpScreen,
        **{k: (lambda k=k, v=v: PlaceholderScreen(k, *v)) for k, v in PLACEHOLDERS.items()},
    }

    def __init__(self, context=None):
        super().__init__()
        self.context = context or AnoteContext()

    def on_mount(self) -> None:
        self.push_screen("home")

    # ---- 导航 ----
    def action_go_home(self):
        self.switch_screen("home")

    def action_go_notes(self):
        self.switch_screen("notes")

    def action_go_queue(self):
        self.switch_screen("queue")

    def action_go_memory(self):
        self.switch_screen("memory")

    def action_go_books(self):
        self.switch_screen("books")

    def action_go_review(self):
        self.switch_screen("review")

    def action_go_settings(self):
        self.switch_screen("settings")

    def action_go_help(self):
        self.switch_screen("help")

    # ---- 动作 ----
    def action_check(self):
        r = self.context.run_script("check.py")
        self.notify(f"自检: {r.tail}", severity="information")

    def on_config_changed(self, message: ConfigChanged) -> None:
        screen = self.screen
        if isinstance(screen, HomeScreen):
            screen.refresh_stats()


def main():
    AnoteApp().run()


if __name__ == "__main__":
    main()
