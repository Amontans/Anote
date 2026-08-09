#!/usr/bin/env python3
"""Anote 数据目录迁移工具：把整个数据目录（含 .git 历史）搬到新位置。

设计要点（docs/TUI-PLAN.md §六）:
  - 源数据在验证通过前绝不删除；失败恢复旧配置（可回滚）
  - .semantic / .venv 为可重建派生物，不随迁，迁移后重建
  - 迁移日志写入 ~/.config/anote/migration.log

用法:
  migrate.py --to <新路径>            # 迁移并更新配置
  migrate.py --to <新路径> --preview   # 仅预览将迁移的条目
  migrate.py --to <新路径> --no-config # 测试模式：迁移但不写配置
"""
import argparse
import datetime
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anote_config import data_dir as cfg_data_dir  # noqa: E402
from anote_config import set as cfg_set  # noqa: E402

EXCLUDE = {".semantic", ".venv"}
LOG_PATH = os.path.expanduser("~/.config/anote/migration.log")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote import cli as _cli  # noqa: E402

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-config", action="store_true")
    ap.add_argument("--with-env", action="store_true", help="迁移后重建 .venv（默认跳过，提示手动）")
    a = ap.parse_args()

    src = os.path.realpath(cfg_data_dir())
    target = os.path.realpath(os.path.expanduser(a.to))
    validate(src, target, a.force)

    if a.preview:
        print(f"源: {src}\n目标: {target}\n\n将迁移（排除 .semantic/.venv）:")
        total = 0
        for name, kind, size in top_items(src):
            print(f"  {'📁' if kind == 'dir' else '📄'} {name}  ({size/1024:.0f} KB)")
            total += size
        print(f"\n共 {len(os.listdir(src))} 项，约 {total/1024/1024:.1f} MB")
        sys.exit(0)

    log(f"开始迁移: {src} → {target}")
    n_before = file_count(src)
    try:
        do_copy(src, target)
    except Exception as e:  # noqa: BLE001
        log(f"复制失败（源未动）: {e}")
        sys.exit(f"✗ 复制失败（源数据未动，安全）: {e}")

    n_after = file_count(target)
    if n_after != n_before:
        log(f"校验失败: 源 {n_before} 文件 vs 目标 {n_after}")
        sys.exit(f"✗ 校验失败: 源 {n_before} vs 目标 {n_after}（源未删除，请检查后重试）")
    log(f"校验通过: {n_after} 个文件一致")

    if not a.no_config:
        try:
            cfg_set("data_dir", target)
        except Exception as e:  # noqa: BLE001
            log(f"配置更新失败: {e}")
            sys.exit(f"✗ 配置更新失败: {e}")

    if a.with_env:
        rebuild_venv(target)

    # 语义索引重建（best-effort）
    if os.path.isdir(os.path.join(src, ".semantic")):
        try:
            env = dict(os.environ, ANOTE_DATA=target)
            py = os.path.join(target, ".venv", "bin", "python") if os.path.exists(os.path.join(target, ".venv", "bin", "python")) else sys.executable
            subprocess.run([py, os.path.join(os.path.dirname(os.path.abspath(__file__)), "embed.py"), "--full"],
                           env=env, timeout=900)
        except Exception as e:  # noqa: BLE001
            log(f"语义索引重建失败（可稍后 anote index-semantic）: {e}")

    # 自检
    try:
        env = dict(os.environ, ANOTE_DATA=target)
        r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "check.py")],
                           env=env, capture_output=True, text=True, timeout=120)
        tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "?"
        log(f"自检: {tail}")
        if "全部正常" not in tail and not a.no_config:
            cfg_set("data_dir", src)  # 回滚配置
            log(f"自检未过，已回滚配置到 {src}")
            sys.exit(f"✗ 自检未过，已回滚配置（源数据未动）: {tail}")
        print(f"✓ 迁移完成: {src} → {target}")
        print(f"  文件 {n_before} 个 | 自检: {tail}")
        if not a.no_config:
            print("  源目录未删除，确认无误后手动删除（保留 = 双保险）")
    except Exception as e:  # noqa: BLE001
        log(f"自检异常: {e}")
        print(f"⚠ 自检异常: {e}（数据已迁移，配置未动）")


if __name__ == "__main__":
    sys.exit(_cli.run(main))
