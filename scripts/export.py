#!/usr/bin/env python3
"""anote export —— 整库打包（可移植/分享）：排除可重建派生物（.venv/.semantic）。

接口声明（契约）:
    输入: argv: [--out 路径] [--with-git]
    输出: stdout=归档路径；退出码 0/1
    副作用: 生成 tar.gz
"""
import os
import sys
import tarfile
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402

EXCLUDE = {".venv", ".semantic", "__pycache__"}


def main() -> int:
    args = sys.argv[1:]
    with_git = "--with-git" in args
    out = None
    if "--out" in args:
        i = args.index("--out")
        if i + 1 < len(args):
            out = args[i + 1]

    data = Path(Config.load().data_dir)
    if not data.is_dir():
        print(f"✗ 数据目录不存在: {data}")
        return 1
    out_path = Path(out) if out else Path.home() / f"anote-export-{date.today().isoformat()}.tar.gz"

    def filt(tarinfo):
        name = Path(tarinfo.name)
        if any(part in EXCLUDE for part in name.parts):
            return None
        if not with_git and ".git" in name.parts:
            return None
        return tarinfo

    with tarfile.open(out_path, "w:gz") as tf:
        tf.add(data, arcname=data.name, filter=filt)
    size = out_path.stat().st_size / 1024 / 1024
    print(f"✓ 已导出: {out_path}（{size:.1f} MB）")
    print("  新机器恢复: 解压 → ~/Documents/Anote → cd ~/Projects/Anote && ./setup.sh → anote check")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
