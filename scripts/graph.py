#!/usr/bin/env python3
"""anote graph —— 知识图谱（薄适配器；逻辑在 services/graph.py）。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.graph import build_graph  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    mermaid = "--mermaid" in args
    limit = 20
    if "--limit" in args:
        i = args.index("--limit")
        if i + 1 < len(args):
            limit = int(args[i + 1])
    g = build_graph(Config.load().data_dir, limit)
    if not g:
        print("（无标签数据：运行 anote meta --ai 补全）")
        return 0
    if mermaid:
        print("```mermaid\n graph LR")
        for tag, refs in g.items():
            for rel, _ in refs:
                print(f'  {tag}["{tag}"] -->|{rel.split("/")[-1]}| N["{rel}"]')
        print("```")
        return 0
    print(f"知识图谱（{len(g)} 个标签节点）\n")
    for tag, refs in g.items():
        print(f"■ {tag}（{len(refs)} 处引用）")
        for rel, c in refs[:8]:
            print(f"    {c}×  {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
