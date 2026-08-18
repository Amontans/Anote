#!/usr/bin/env python3
"""anote init-data —— 初始化数据目录骨架（幂等，不覆盖已有文件）。

接口声明（契约）:
    输入: 无（ANOTE_DATA 或默认数据根）
    输出: stdout=创建统计；退出码 0
    副作用: 仅创建缺失目录/文件
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.bootstrap import ensure_data_dir  # noqa: E402


def main() -> int:
    data = Config.load().data_dir
    r = ensure_data_dir(data)
    print(f"✓ 数据目录就绪: {data}")
    print(f"  新建目录 {r['created_dirs']} 个，新建文件 {r['created_files']} 个")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
