#!/usr/bin/env python3
"""anote bibcheck —— 引用链路校验（v1.3）：笔记 cite 与 refs.bib 一致性。

接口声明（契约）:
    输入: argv（无）
    输出: stdout=报告；退出码 0 正常 / 1 有缺失
    副作用: 无（只读）
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import BibService  # noqa: E402


def main() -> int:
    data = Config.load().data_dir
    bib = BibService(data)
    missing = bib.missing()
    unused = bib.unused()
    print(f"引用链路校验: {bib.refs}")
    print(f"  refs.bib 条目: {len(bib.keys())} | 笔记引用键: {len(bib.cited_keys())}")
    if missing:
        print(f"\n⚠️ 缺失 {len(missing)} 个引用键（笔记引用了但 bib 没有）:")
        for k in missing:
            print(f"  ✗ {k}")
    else:
        print("\n✓ 所有引用键均在 refs.bib 中")
    if unused:
        print(f"\nℹ️ 未被引用的 bib 条目 {len(unused)} 个（可能冗余，可清理）:")
        print("  " + ", ".join(unused[:15]))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
