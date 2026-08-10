#!/usr/bin/env python3
"""anote check —— 一致性自检（薄适配器；逻辑在 services/health.py）。

接口声明（契约）:
    输入: argv（无）
    输出: stdout=7 项报告；退出码 0（报告型）
    副作用: 无
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import HealthService  # noqa: E402


def main() -> int:
    results = HealthService(Config.load().data_dir).run()
    problems = 0
    print("=== 知识库自检 ===")
    for ok, msg in results:
        print(msg)
        if not ok:
            problems += 1
    print("\n=== 结果 ===")
    if problems:
        print(f"⚠️ 共 {problems} 项需处理（可让 Pi 协助修复）")
    else:
        print("✅ 全部正常")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
