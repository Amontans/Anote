#!/usr/bin/env python3
"""写操作集成测试（临时数据目录，不碰真实数据）：新建笔记/队列状态/记忆追加/回顾/新书。"""
import asyncio
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from tui.anote_app import AnoteApp

TMP = tempfile.mkdtemp(prefix="anote-act-")


def setup():
    os.environ["ANOTE_DATA"] = TMP
    from anote.services.bootstrap import ensure_data_dir
    ensure_data_dir(TMP)
    with open(os.path.join(TMP, "queue.md"), "w", encoding="utf-8") as f:
        f.write("# 队列\n\n| 状态 | 日期 | 论文 | ID | 笔记 |\n|------|------|------|----|------|\n| 📥 | 2026-08-09 | 测试论文 | 2401.00001 | — |\n")


async def main():
    setup()
    try:
        app = AnoteApp()
        async with app.run_test() as pilot:
            # 1) 新建笔记
            await pilot.press("ctrl+n")
            notes = app.screen
            notes._new("数学/代数> 测试笔记")
            await pilot.pause(0.5)
            created = os.path.join(TMP, "src/数学/代数")
            files = os.listdir(created)
            assert any(f.endswith(".tex") for f in files), f"笔记未创建: {files}"
            print("✓ 新建笔记")

            # 2) 队列状态切换
            await pilot.press("ctrl+q")
            queue = app.screen
            queue.action_cycle()
            await pilot.pause(0.3)
            q = open(os.path.join(TMP, "queue.md"), encoding="utf-8").read()
            assert "| 📖 |" in q, "队列状态未切换"
            print("✓ 队列状态切换")

            # 3) 记忆追加
            await pilot.press("ctrl+m")
            mem = app.screen
            mem._append("这是测试洞见")
            await pilot.pause(0.3)
            content = open(os.path.join(TMP, "memory/research-log.md"), encoding="utf-8").read()
            assert "测试洞见" in content
            print("✓ 记忆追加（研究日志页签）")

            # 4) 生成回顾
            await pilot.press("ctrl+r")
            rev = app.screen
            rev.action_generate()
            await pilot.pause(0.5)
            drafts = os.listdir(os.path.join(TMP, "memory/reviews"))
            assert any(f.endswith(".md") for f in drafts), f"回顾未生成: {drafts}"
            print("✓ 回顾生成")

            # 5) 新建书
            await pilot.press("ctrl+b")
            books = app.screen
            books._new_book("测试书")
            await pilot.pause(0.3)
            assert os.path.isdir(os.path.join(TMP, "books/测试书/chapters"))
            print("✓ 新建教科书")

        print("ACTIONS OK: 全部写操作通过")
    finally:
        os.environ.pop("ANOTE_DATA", None)
        shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
