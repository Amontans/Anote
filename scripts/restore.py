#!/usr/bin/env python3
"""anote restore —— 备份恢复/演练（薄适配器；逻辑在 services/restore.py）。

接口声明（契约）:
    输入: <备份文件> [--dry-run] [--force] [--to 目录] [--key 口令]
    输出: stdout=校验/恢复报告；退出码 0/1
    副作用: --force 时安全解包到目标目录
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.restore import restore_backup  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print("用法: anote restore <备份文件> [--dry-run] [--force] [--to 目录] [--key 口令]")
        return 1
    path = Path(os.path.expanduser(args[0]))
    dry = "--dry-run" in args
    force = "--force" in args
    to = None
    if "--to" in args:
        i = args.index("--to")
        if i + 1 < len(args):
            to = Path(os.path.expanduser(args[i + 1]))
    key = None
    if "--key" in args:
        i = args.index("--key")
        if i + 1 < len(args):
            key = args[i + 1]

    target = to or Config.load().data_dir
    report = restore_backup(path, target, dry_run=dry, force=force, key=key)
    print(report.message)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
