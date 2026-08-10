#!/usr/bin/env python3
"""anote bibcheck —— 引用链路校验（v1.3）：笔记 cite 命令与 refs.bib 一致性。

检查:
  1. refs.bib 缺失的引用键（笔记引了但 bib 没有 → 编译会报错）
  2. refs.bib 中未被引用的条目（可能冗余）

接口声明（契约）:
    输入: argv（无）
    输出: stdout=报告；退出码 0 正常 / 1 有问题
    副作用: 无（只读）
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import NotesService  # noqa: E402

BIB_ENTRY = re.compile(r"@\w+\{([^,]+),", re.M)
CITE = re.compile(r"\\cite[tp]?\*?\{([^}]+)\}")


def parse_bib(path: Path) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {m.group(1).strip() for m in BIB_ENTRY.finditer(text)}


def cited_keys(data: Path) -> set[str]:
    keys = set()
    for root, _, fs in os.walk(Path(data) / "src"):
        for f in fs:
            if not f.endswith(".tex"):
                continue
            try:
                text = (Path(root) / f).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for m in CITE.finditer(text):
                for k in m.group(1).split(","):
                    keys.add(k.strip())
    return keys


def main() -> int:
    data = Config.load().data_dir
    refs = Path(data) / "refs.bib"
    bib = parse_bib(refs)
    cited = cited_keys(data)
    missing = sorted(cited - bib)
    unused = sorted(bib - cited)
    print(f"引用链路校验: {refs}")
    print(f"  refs.bib 条目: {len(bib)} | 笔记引用键: {len(cited)}")
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
