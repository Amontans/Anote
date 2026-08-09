#!/usr/bin/env python3
"""Anote 统计（薄适配器）：逻辑在 src/anote/services.py。"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import StatsService  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote import cli as _cli  # noqa: E402

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    stats = StatsService(Config.load().data_dir).compute()
    if a.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return
    q = stats.pop("队列")
    print(f"数据目录: {Config.load().data_dir}\n")
    print(f"  📝 笔记总数     {stats['笔记总数']}")
    print(f"  📄 论文精读     {stats['论文精读']}")
    print(f"  📚 教科书       {stats['教科书']}（章节 {stats['章节']}）")
    print(f"  📁 项目         {stats['项目']}")
    print(f"  🔄 回顾草稿     {stats['回顾草稿']}")
    print(f"  📥 队列         " + " ".join(f"{k}{q.get(k, 0)}" for k in ("📥", "📖", "✅", "🗄")))
    print(f"  🗂️ PDF 附件     {stats['PDF 附件']}")
    print(f"  📦 编译产物 PDF {stats['编译产物 PDF']}")


if __name__ == "__main__":
    sys.exit(_cli.run(main))
