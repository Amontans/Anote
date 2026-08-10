#!/usr/bin/env python3
"""anote review —— 回顾草稿（薄适配器；逻辑在 services/review.py）。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.review import ReviewService  # noqa: E402


def main() -> int:
    days = 7
    args = sys.argv[1:]
    out = None
    if "--days" in args:
        i = args.index("--days")
        if i + 1 < len(args):
            days = int(args[i + 1])
    if "--out" in args:
        i = args.index("--out")
        if i + 1 < len(args):
            out = args[i + 1]
    path, n, papers = ReviewService(Config.load().data_dir).generate(days, out)
    print(f"回顾草稿已生成: {path}")
    print(f"本周期改动文件 {n} 个（论文 {papers} 篇）")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
