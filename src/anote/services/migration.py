from __future__ import annotations

"""数据迁移领域服务：数据目录搬迁（含 .git）、校验、回滚（migrate.py 薄适配器）。

安全: 源在验证前不删；失败恢复旧配置。
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


import datetime

EXCLUDE = {".semantic", ".venv"}
LOG_PATH = Path("~/.config/anote/migration.log").expanduser()


def log(msg):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now().isoformat()}] {msg}\n")


def file_count(root, excluded=EXCLUDE):
    n = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in excluded]
        n += len(filenames)
    return n


def top_items(src):
    items = []
    for name in sorted(os.listdir(src)):
        p = os.path.join(src, name)
        if name in EXCLUDE:
            continue
        if os.path.isdir(p):
            size = sum(os.path.getsize(os.path.join(r, f))
                       for r, _, fs in os.walk(p) for f in fs)
            items.append((name, "dir", size))
        else:
            items.append((name, "file", os.path.getsize(p)))
    return items


def validate(src, target, force):
    if os.path.realpath(src) == os.path.realpath(target):
        sys.exit("目标路径与当前数据目录相同")
    if os.path.commonpath([os.path.realpath(src), os.path.realpath(target)]) == os.path.realpath(src):
        sys.exit("目标不能位于当前数据目录内部")
    if os.path.exists(target):
        if not force:
            existing = [n for n in os.listdir(target) if n not in EXCLUDE]
            if existing:
                sys.exit(f"目标目录非空（{len(existing)} 项），加 --force 继续（会合并）")


def do_copy(src, target):
    shutil.copytree(src, target, ignore=shutil.ignore_patterns(*EXCLUDE),
                    dirs_exist_ok=True)


def rebuild_venv(target):
    """重建 .venv（可重建派生物，失败仅警告）。"""
    venv = os.path.join(target, ".venv")
    try:
        subprocess.run(["python3", "-m", "venv", venv], check=True, timeout=120)
        subprocess.run([os.path.join(venv, "bin", "pip"), "install", "-q",
                        "fastembed", "numpy", "textual"], check=True, timeout=600)
        return True
    except Exception as e:  # noqa: BLE001
        log(f"venv 重建失败（可稍后 anote setup 处理）: {e}")
        return False


