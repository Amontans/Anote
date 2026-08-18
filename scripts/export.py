#!/usr/bin/env python3
"""anote export —— 整库打包（可移植/分享）：排除运行产物（.venv/.semantic 等）。

接口声明（契约）:
    输入: [--out 路径] [--with-git]
    输出: stdout=归档路径；退出码 0/1
    副作用: 默认生成 <数据根>/.anote/exports/anote-export-<日期>.tar.gz
"""
import os
import sys
import tarfile
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config, export_dir_for  # noqa: E402

EXCLUDE_PARTS = {".venv", ".semantic", "__pycache__"}
EXCLUDE_REL = {".anote/logs", ".anote/backups", ".anote/exports", ".anote/previews", ".anote/migration.log"}


def main() -> int:
    args = sys.argv[1:]
    with_git = "--with-git" in args
    data = Path(Config.load().data_dir)
    if not data.is_dir():
        print(f"✗ 数据目录不存在: {data}")
        return 1

    out = None
    if "--out" in args:
        i = args.index("--out")
        if i + 1 < len(args):
            out = args[i + 1]
    out_path = Path(os.path.expanduser(out)) if out else \
        export_dir_for(data) / f"anote-export-{date.today().isoformat()}.tar.gz"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    def filt(tarinfo):
        name = Path(tarinfo.name)
        parts = name.parts
        rel = Path(*parts[1:]) if len(parts) > 1 and parts[0] == data.name else name
        if any(part in EXCLUDE_PARTS for part in rel.parts):
            return None
        if str(rel) in EXCLUDE_REL or any(rel.is_relative_to(Path(x)) for x in EXCLUDE_REL):
            return None
        if not with_git and ".git" in rel.parts:
            return None
        return tarinfo

    with tarfile.open(out_path, "w:gz") as tf:
        tf.add(data, arcname=data.name, filter=filt)
    size = out_path.stat().st_size / 1024 / 1024
    print(f"✓ 已导出: {out_path}（{size:.1f} MB）")
    print("  新机器恢复: 解压 → 数据根目录 → 项目目录 ./setup.sh → anote check")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
