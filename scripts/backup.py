#!/usr/bin/env python3
"""anote backup-create —— 加密/校验备份（薄适配器；逻辑在 services/backup.py）。

接口声明（契约）:
    输入: [--out 目录] [--encrypt] [--no-git]
    输出: stdout=备份路径+校验和；退出码 0/1
    副作用: 写备份文件（默认 .anote/backups）
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.backup import create_backup  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    encrypt = "--encrypt" in args
    with_git = "--no-git" not in args
    out_dir = None
    if "--out" in args:
        i = args.index("--out")
        if i + 1 < len(args):
            out_dir = Path(os.path.expanduser(args[i + 1]))
    try:
        r = create_backup(Config.load().data_dir, out_dir,
                          encrypt=encrypt, with_git=with_git)
    except FileNotFoundError as e:
        print(f"✗ {e}")
        return 1
    print(f"✓ 备份完成: {r.path}（{r.size_mb:.1f} MB）")
    print(f"  SHA256: {r.digest[:16]}…")
    print(f"  （还原: anote restore {r.path} --dry-run 演练 / --force 执行）")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
