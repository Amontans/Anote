#!/usr/bin/env python3
"""无头冒烟测试：验证屏幕导航/命令面板/自检动作（Textual Pilot，可在无终端环境运行）。"""
import asyncio

from tui.anote_app import AnoteApp
from tui.screens.help import HelpScreen
from tui.screens.home import HomeScreen
from tui.screens.placeholders import PlaceholderScreen
from tui.screens.settings import SettingsScreen


async def main():
    app = AnoteApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, HomeScreen), f"初始应为 Home, 实际 {type(app.screen)}"
        await pilot.press("ctrl+s")
        assert isinstance(app.screen, SettingsScreen)
        await pilot.press("ctrl+h")
        assert isinstance(app.screen, HomeScreen)
        await pilot.press("f1")
        assert isinstance(app.screen, HelpScreen)
        await pilot.press("ctrl+h")
        await pilot.press("ctrl+n")
        assert isinstance(app.screen, PlaceholderScreen) and app.screen._key == "notes"
        await pilot.press("ctrl+q")
        assert app.screen._key == "queue"
        await pilot.press("ctrl+m")
        assert app.screen._key == "memory"
        await pilot.press("ctrl+b")
        assert app.screen._key == "books"
        await pilot.press("ctrl+r")
        assert app.screen._key == "review"
        await pilot.press("ctrl+s")
        assert isinstance(app.screen, SettingsScreen)
        # 命令面板
        await pilot.press("ctrl+p")
        await pilot.pause(0.3)
        await pilot.press("escape")
        # 自检动作
        await pilot.press("ctrl+h")
        await pilot.press("f5")
        await pilot.pause(0.2)
        print("SMOKE OK: 屏幕导航/面板/动作全部通过")


if __name__ == "__main__":
    asyncio.run(main())
