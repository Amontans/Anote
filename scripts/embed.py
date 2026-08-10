#!/usr/bin/env python3
"""anote 语义索引构建（薄适配器；逻辑在 services/semantic.py）。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.semantic import SemanticService  # noqa: E402


def main() -> int:
    full = "--full" in sys.argv[1:]
    svc = SemanticService(Config.load().data_dir)
    total, new = svc.build(full=full)
    if new:
        print(f"✓ 语义索引完成：{total} 块（新增 {new}）→ {svc.cache}")
    else:
        print(f"✓ 语义索引已是最新（{total} 块）")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
