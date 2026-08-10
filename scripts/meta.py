#!/usr/bin/env python3
"""anote meta —— META 检查/补全（薄适配器；逻辑在 services/meta.py）。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config, ai_ask  # noqa: E402
from anote.services import NotesService  # noqa: E402
from anote.services.meta import audit  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    ai_mode = "--ai" in args
    notes = NotesService(Config.load().data_dir).scan()
    missing_meta, missing_fields = audit(notes)
    print(f"META 检查（{len(notes)} 篇笔记）")
    print(f"  ✓ 完整: {len(notes) - len(missing_meta) - len({id(n) for n, _ in missing_fields})} "
          f"| 缺 META: {len(missing_meta)} | 缺字段: {len(missing_fields)}")
    if missing_meta:
        print("\n⚠️ 完全缺 META:")
        for n in missing_meta:
            print(f"  ✗ {n.rel}")
    if missing_fields:
        print("\n⚠️ 缺字段:")
        for n, f in missing_fields[:20]:
            print(f"  • {f}: {n.rel}")
    if ai_mode and (missing_meta or missing_fields):
        print("\n── 经 Pi 生成补全建议 ──")
        target = missing_meta + [n for n, _ in missing_fields][:20]
        prompt = ("你是 Anote 笔记的元数据助手。请为以下笔记生成 META 头补全建议。\n"
                  + "\n".join(f"- {n.rel}（现有 META: {n.meta or '无'}）" for n in target)
                  + "\n\nMETA 格式: % ==META== 学科: X | 分支: Y | 标签: a,b | 日期: YYYY-MM-DD | 来源: 教材/论文/其他\n"
                    "输出: 每个文件一行: <路径> ===> <完整 META 行>。只输出这些行。")
        r = ai_ask(prompt)
        print(r.stdout if r.ok else f"✗ Pi 调用失败: {r.stderr}")
        return 0 if r.ok else 1
    if ai_mode:
        print("\n✓ 所有笔记 META 完整")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
