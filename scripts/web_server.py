#!/usr/bin/env python3
"""anote web —— 只读浏览外壳（薄适配器；逻辑在 services/webserver.py）。

接口声明（契约）:
    输入: [--port N] [--token xxx]
    输出: HTTP；退出码 0/1
    副作用: 无（只读；禁止访问 .git/.venv/.semantic/.anote）
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.webserver import serve  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--token", default=None)
    a = ap.parse_args()
    serve(Config.load().data_dir, port=a.port, token=a.token)
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
