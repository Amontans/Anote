#!/usr/bin/env python3
"""无头冒烟测试：导航 + 各数据页挂载 + 只读交互（不修改真实数据）。"""
import asyncio
import os
import shutil
import tempfile

from tui.anote_app import AnoteApp
from tui.screens.ask import AskScreen
from tui.screens.books import BooksScreen
from tui.screens.help import HelpScreen
from tui.screens.home import HomeScreen
from tui.screens.memory import MemoryScreen
from tui.screens.notes import NotesScreen
from tui.screens.queue import QueueScreen
from tui.screens.review import ReviewScreen
from tui.screens.search import SearchScreen
from tui.screens.settings import SettingsScreen

# 用临时数据目录隔离（不碰真实数据）
import anote_config

TMP = tempfile.mkdtemp(prefix="anote-test-")


def setup_module():
    os.environ["ANOTE_DATA"] = TMP
    for d in ["src/数学/代数", "memory/reviews", "books", "projects", "pdfs"]:
        os.makedirs(os.path.join(TMP, d), exist_ok=True)
    with open(os.path.join(TMP, "src/数学/代数/群论基础.tex"), "w", encoding="utf-8") as f:
        f.write("% ==META== 学科: 数学 | 分支: 代数 | 标签: 群 | 日期: 2026-08-09 | 来源: 教材\n\\documentclass{ctexart}\n\\begin{document}\n\\section{群}\n群是集合配合二元运算。\n\\end{document}\n")
    with open(os.path.join(TMP, "queue.md"), "w", encoding="utf-8") as f:
        f.write("# 队列\n\n| 状态 | 日期 | 论文 | ID | 笔记 |\n|------|------|------|----|------|\n| 📥 | 2026-08-09 | 测试论文 | 2401.00001 | — |\n")
    with open(os.path.join(TMP, "memory/research-log.md"), "w", encoding="utf-8") as f:
        f.write("# 研究日志\n\n## 2026-08-09\n- 测试\n")
    for n in ["insights.md", "concepts.md", "open-questions.md"]:
        with open(os.path.join(TMP, f"memory/{n}"), "w", encoding="utf-8") as f:
            f.write(f"# {n}\n")
    shutil.copytree(os.path.join(os.path.expanduser("~/Documents/Anote"), "books", "_template"), os.path.join(TMP, "books", "_template"))
    shutil.copy(os.path.join(os.path.expanduser("~/Documents/Anote"), "books", "_template", "chapters", "ch01.tex"),
                os.path.join(TMP, "books", "_template", "chapters", "ch01.tex"))


async def main():
    setup_module()
    try:
        app = AnoteApp()
        async with app.run_test() as pilot:
            assert isinstance(app.screen, HomeScreen)
            await pilot.press("ctrl+n"); assert isinstance(app.screen, NotesScreen)
            await pilot.pause(0.2)
            await pilot.press("ctrl+q"); assert isinstance(app.screen, QueueScreen)
            await pilot.pause(0.2)
            await pilot.press("ctrl+m"); assert isinstance(app.screen, MemoryScreen)
            await pilot.pause(0.2)
            await pilot.press("ctrl+b"); assert isinstance(app.screen, BooksScreen)
            await pilot.pause(0.2)
            await pilot.press("ctrl+r"); assert isinstance(app.screen, ReviewScreen)
            await pilot.pause(0.2)
            await pilot.press("ctrl+s"); assert isinstance(app.screen, SettingsScreen)
            await pilot.press("ctrl+f"); assert isinstance(app.screen, SearchScreen)
            await pilot.press("ctrl+a"); assert isinstance(app.screen, AskScreen)
            await pilot.press("ctrl+h"); assert isinstance(app.screen, HomeScreen)
            await pilot.press("f1"); assert isinstance(app.screen, HelpScreen)
            await pilot.press("ctrl+h"); assert isinstance(app.screen, HomeScreen)
            await pilot.press("f5")
            await pilot.pause(0.2)
            print("SMOKE OK: 10 屏导航 + 挂载全部通过")
    finally:
        os.environ.pop("ANOTE_DATA", None)
        shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
