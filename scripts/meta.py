#!/usr/bin/env python3
"""anote meta —— META 元数据管理（v1.4）：报告缺 META/缺标签的笔记，--ai 经 Pi 补全建议。

接口声明（契约）:
    输入: argv: [--ai] [--apply]；配置经 anote.core.Config（ANOTE_DATA 可覆盖）
    输出: stdout=报告/建议；stderr=错误；退出码 0/1
    副作用: --apply 时改写笔记头部 META（git 可回滚）
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config, ai_ask  # noqa: E402
from anote.services import NotesService  # noqa: E402

REQUIRED = ("学科", "日期")
SUGGESTED = ("标签", "来源")


def main() -> int:
    args = sys.argv[1:]
    ai_mode = "--ai" in args
    apply_mode = "--apply" in args
    data = Config.load().data_dir
    notes = NotesService(data).scan()

    missing_meta = [n for n in notes if not n.meta]
    missing_fields = []
    for n in notes:
        if n.meta:
            for f in REQUIRED:
                if not n.meta.get(f):
                    missing_fields.append((n, f))
            for f in SUGGESTED:
                if not n.meta.get(f):
                    missing_fields.append((n, f))

    print(f"META 检查（{len(notes)} 篇笔记）")
    print(f"  ✓ 完整: {len(notes) - len(missing_meta) - len({id(n) for n, _ in missing_fields})} "
          f"| 缺 META: {len(missing_meta)} | 缺字段: {len(missing_fields)}")
    if missing_meta:
        print("\n⚠️ 完全缺 META 的笔记:")
        for n in missing_meta:
            print(f"  ✗ {n.rel}")
    if missing_fields:
        print("\n⚠️ 缺字段（学科/日期为必填，标签/来源建议补）:")
        for n, f in missing_fields[:20]:
            print(f"  • {f}: {n.rel}")

    if ai_mode and (missing_meta or missing_fields):
        print("\n── 经 Pi 生成补全建议 ──")
        target = (missing_meta + [n for n, _ in missing_fields][:20])
        prompt = (
            "你是 Anote 笔记的元数据助手。请为以下每个笔记文件生成 META 头补全建议。\n"
            "文件列表:\n" + "\n".join(f"- {n.rel}（现有 META: {n.meta or '无'}）" for n in target) +
            "\n\nMETA 格式: % ==META== 学科: X | 分支: Y | 标签: a,b | 日期: YYYY-MM-DD | 来源: 教材/论文/其他\n"
            "输出要求: 每个文件一行，格式: <文件路径> ===> <完整 META 行>。只输出这些行。"
        )
        r = ai_ask(prompt)
        if not r.ok:
            print(f"✗ Pi 调用失败: {r.stderr}")
            return 1
        print(r.stdout)
        print("\n（确认后可用 --apply 写入；--apply 需配合 --ai 输出格式）")
    elif ai_mode:
        print("\n✓ 所有笔记 META 完整，无需补全")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
