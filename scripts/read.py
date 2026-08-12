#!/usr/bin/env python3
"""anote read —— 统一阅读入口（v1.9.1）：PDF/epub/mobi 用对应阅读器打开。

接口声明（契约）:
    输入: <相对数据目录的路径>
    输出: stdout=打开信息；退出码 0/1
    副作用: 启动外部阅读器
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.ebooks import pick_reader  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("用法: anote read <路径>（如 anote read pdfs/2402.00001.pdf 或 ebooks/xxx.epub）")
        return 1
    data = Path(Config.load().data_dir)
    p = data / args[0]
    if not p.exists():
        print(f"✗ 不存在: {p}")
        return 1
    reader = pick_reader(p, Config.load().config.get("reader", ""))
    subprocess.Popen([reader, str(p)], start_new_session=True)
    print(f"✓ 用 {reader} 打开: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
