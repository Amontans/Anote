#!/usr/bin/env python3
"""anote new —— 新建笔记（薄适配器；逻辑在 services/notes.py）。

接口声明（契约）:
    输入: <学科/分支> <标题> [--template note|note-math] [--no-edit]
    输出: stdout=创建路径；stderr=错误；退出码 0/1
    副作用: 写 <数据根>/src/<学科/分支>/<日期>_<标题>.tex；默认用配置编辑器打开
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import NotesService  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    pos = [a for a in args if not a.startswith("--")]
    if len(pos) < 2:
        print("用法: anote new <学科/分支> <标题> [--template note|note-math]", file=sys.stderr)
        return 1
    subject, title = pos[0], " ".join(pos[1:])
    template = "note"
    if "--template" in args:
        i = args.index("--template")
        if i + 1 < len(args):
            template = args[i + 1]
    try:
        path = NotesService(Config.load().data_dir).create(
            subject, title, template=template,
            open_editor="--no-edit" not in args)
    except (ValueError, FileExistsError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 1
    print(f"✓ 已创建: {path}（模板: {template}）")
    print('  💡 下一步: 写完 anote commit "说明"（自动索引+自检）')
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
