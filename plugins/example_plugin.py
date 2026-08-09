#!/usr/bin/env python3
"""示例插件：打印今日日期与笔记数。

接口声明（契约）:
    输入: argv（无）
    输出: stdout=信息；退出码 0
    副作用: 无
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import NotesService  # noqa: E402


def main() -> int:
    data = Config.load().data_dir
    n = len(NotesService(data).scan())
    print(f"📅 {date.today().isoformat()} | 数据目录: {data} | 笔记 {n} 篇")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
