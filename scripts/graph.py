#!/usr/bin/env python3
"""anote graph —— 知识图谱数据（v1.6）：META 标签 + 反链聚合。

输出:
  默认: 邻接表（标签/概念 → 引用它的笔记，按次数）
  --mermaid: mermaid flowchart（可粘贴到支持 mermaid 的工具/网页）
接口声明（契约）:
    输入: argv: [--mermaid] [--limit N]
    输出: stdout=图谱数据；退出码 0/1
    副作用: 无（只读）
"""
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import NotesService  # noqa: E402


def build_graph(data: Path, limit: int = 20) -> dict[str, list[tuple[str, int]]]:
    """标签/概念 → [(引用笔记 rel, 出现次数)]（基于 META 标签 + 文件名）。"""
    notes = NotesService(data).scan()
    g: dict[str, list] = defaultdict(list)
    for n in notes:
        tags = [t.strip() for t in (n.meta.get("标签") or "").split(",") if t.strip()]
        for t in tags:
            g[t].append((n.rel, 1))
        # 反链：其他笔记 META/标题提及该笔记主题词？简化为标签为主
    # 聚合次数并排序
    return {k: sorted(v, key=lambda x: -x[1])[:limit] for k, v in sorted(g.items())}


def main() -> int:
    args = sys.argv[1:]
    mermaid = "--mermaid" in args
    limit = 20
    if "--limit" in args:
        i = args.index("--limit")
        if i + 1 < len(args):
            limit = int(args[i + 1])
    data = Config.load().data_dir
    g = build_graph(data, limit)
    if not g:
        print("（无标签数据：笔记 META 标签为空，运行 anote meta --ai 补全）")
        return 0
    if mermaid:
        print("```mermaid")
        print("graph LR")
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
