from __future__ import annotations

"""数据迁移领域服务：数据目录搬迁（含 .git/.anote 配置）、校验、回滚。"""

import datetime
import os
import shutil
import subprocess
from pathlib import Path

from ..core import (PROJECT_ROOT, Config, migration_log_path_for,
                    update_data_dir_pointer)

EXCLUDE_PARTS = {".semantic", ".venv", "__pycache__"}
# 运行产物不迁移；配置与 external.json 会随迁
EXCLUDE_REL = {".anote/logs", ".anote/backups", ".anote/exports", ".anote/previews", ".anote/migration.log"}


def log(msg, data_dir=None):
    """迁移日志：<数据根>/.anote/migration.log。"""
    root = Path(data_dir) if data_dir else Config.load().data_dir
    path = migration_log_path_for(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now().isoformat()}] {msg}\n")


def _skip(root: Path) -> bool:
    parts = root.parts
    if any(p in EXCLUDE_PARTS for p in parts):
        return True
    if ".anote" in parts:
        i = parts.index(".anote")
        rel = Path(*parts[i:])
        if str(rel) in EXCLUDE_REL or any(rel.is_relative_to(Path(x)) for x in EXCLUDE_REL):
            return True
    return False


def _iter_files(root):
    """遍历数据根下的普通文件（过滤运行产物）。"""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not _skip(Path(dirpath) / d)]
        for f in filenames:
            p = Path(dirpath) / f
            if not _skip(p):
                yield p


def file_count(root, excluded=None):
    return sum(1 for _ in _iter_files(root))


def top_items(src):
    items = []
    for name in sorted(os.listdir(src)):
        p = os.path.join(src, name)
        if _skip(Path(p)):
            continue
        if os.path.isdir(p):
            size = sum(p.stat().st_size for p in _iter_files(p))
            items.append((name, "dir", size))
        else:
            items.append((name, "file", os.path.getsize(p)))
    return items


def validate(src, target, force):
    if os.path.realpath(src) == os.path.realpath(target):
        sys_exit("目标路径与当前数据目录相同")
    if os.path.commonpath([os.path.realpath(src), os.path.realpath(target)]) == os.path.realpath(src):
        sys_exit("目标不能位于当前数据目录内部")
    if os.path.exists(target):
        if not force:
            existing = [n for n in os.listdir(target) if n not in EXCLUDE_PARTS]
            if existing:
                sys_exit(f"目标目录非空（{len(existing)} 项），加 --force 继续（会合并）")


def sys_exit(msg):
    print(msg)
    raise SystemExit(1)


def _ignore(dirpath, names):
    out = set()
    for n in names:
        p = Path(dirpath) / n
        if _skip(p):
            out.add(n)
    return out


def do_copy(src, target):
    shutil.copytree(src, target, ignore=_ignore, dirs_exist_ok=True)


def finalize_config(target: Path) -> None:
    """把配置写到目标数据根，并更新 ~/.config/anote/config 定位指针。"""
    cfg = Config.load()
    cfg.data_dir = target
    cfg.save()
    # 即使运行在 ANOTE_DATA 环境下也更新指针，保证设置页迁移后能找到新数据根
    update_data_dir_pointer(target, force=True)


def install_hooks(target: Path) -> None:
    git_dir = target / ".git"
    if not git_dir.is_dir():
        return
    hooks = git_dir / "hooks"
    hooks.mkdir(exist_ok=True)
    for name in ("pre-commit", "pre-push"):
        src = PROJECT_ROOT / "config" / "git-hooks" / name
        if src.exists():
            shutil.copyfile(src, hooks / name)
            os.chmod(hooks / name, 0o755)


def rebuild_venv(target):
    """重建 .venv（可重建派生物，失败仅警告）。"""
    venv = os.path.join(target, ".venv")
    try:
        subprocess.run(["python3", "-m", "venv", venv], check=True, timeout=120)
        subprocess.run([os.path.join(venv, "bin", "pip"), "install", "-q",
                        "-r", str(PROJECT_ROOT / "requirements.txt")], check=True, timeout=600)
        return True
    except Exception as e:  # noqa: BLE001
        log(f"venv 重建失败（可稍后 setup.sh 处理）: {e}", data_dir=target)
        return False
