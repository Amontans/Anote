#!/usr/bin/env python3
"""anote paper —— 论文/综述/开题骨架生成（薄适配器；逻辑在 services/paper.py）。

接口声明（契约）:
    输入: <主题> [--type 论文|综述|开题] [--no-ai] [--dry]
    输出: stdout=素材/骨架报告；退出码 0/1
    副作用: 写 projects/<主题>/{paper.tex, materials.md}；--dry 不写
"""
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.paper import TYPES, collect_materials, generate  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print("用法: anote paper <主题> [--type 论文|综述|开题] [--no-ai] [--dry]")
        return 1
    topic = args[0]
    type_cn = "论文"
    if "--type" in args:
        i = args.index("--type")
        if i + 1 < len(args):
            type_cn = args[i + 1]
    use_ai = "--no-ai" not in args
    dry = "--dry" in args

    data = Path(Config.load().data_dir)
    print(f"═══ 论文素材聚合: 《{topic}》（{type_cn}）═══")
    materials = collect_materials(topic, data)
    print(f"  相关笔记 {len(materials['notes'])} | 引用 {len(materials['refs'])} | wiki 主题页 {len(materials['wiki'])}")
    for n in materials["notes"][:5]:
        print(f"    • {n}")
    if dry:
        print("\n（--dry：仅素材聚合，未生成骨架）")
        return 0
    tex, note = generate(topic, type_cn, materials, data, use_ai=use_ai)
    print(f"\n✓ 骨架已生成: {tex}  {note}")
    print(f"  📎 素材包: {tex.parent / 'materials.md'}")
    print(f"  （编译: cd {tex.parent} && latexmk -lualatex paper.tex；引用需 refs.bib 在上级或 BIBINPUTS）")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
