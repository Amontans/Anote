#!/usr/bin/env python3
"""anote migrate —— 数据目录迁移（薄适配器；逻辑在 services/migration.py）。

含 .git 与 .anote 配置；运行产物（.semantic/.venv/日志/备份）不迁移。
接口声明（契约）:
    输入: --to <路径> [--preview] [--force] [--no-config] [--with-env]
    输出: stdout=迁移报告；退出码 0/1
    副作用: 复制数据；成功后目标成为新配置位置，源目录保留（双保险）
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import migration as mig  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    if "--to" not in args:
        print("用法: anote migrate --to <新路径> [--preview] [--force] [--no-config] [--with-env]")
        return 1
    to = args[args.index("--to") + 1]
    preview = "--preview" in args
    force = "--force" in args
    no_config = "--no-config" in args
    with_env = "--with-env" in args

    src = Path(Config.load().data_dir).resolve()
    target = Path(to).expanduser().resolve()
    try:
        mig.validate(src, target, force)
    except SystemExit as e:
        return int(e.code or 1)
    if preview:
        items = mig.top_items(src)
        print(f"源: {src}\n目标: {target}\n\n将迁移（排除 .semantic/.venv/运行日志/备份）:")
        total = 0
        for name, kind, size in items:
            print(f"  {'📁' if kind == 'dir' else '📄'} {name}  ({size/1024:.0f} KB)")
            total += size
        print(f"\n共 {len(items)} 项，约 {total/1024/1024:.1f} MB")
        return 0

    mig.log(f"开始迁移: {src} → {target}", data_dir=src)
    n_before = mig.file_count(src)
    try:
        mig.do_copy(src, target)
    except Exception as e:  # noqa: BLE001
        mig.log(f"复制失败（源未动）: {e}", data_dir=src)
        print(f"✗ 复制失败（源数据未动，安全）: {e}")
        return 1
    n_after = mig.file_count(target)
    if n_after != n_before:
        mig.log(f"校验失败: 源 {n_before} vs 目标 {n_after}", data_dir=src)
        print(f"✗ 校验失败: 源 {n_before} vs 目标 {n_after}（源未删除）")
        return 1

    if not no_config:
        mig.finalize_config(target)
    mig.install_hooks(target)
    mig.log(f"迁移完成: {src} → {target}（文件 {n_before} 个；源保留=双保险）", data_dir=target)

    if with_env:
        mig.rebuild_venv(target)
    if (src / ".semantic").is_dir():
        try:
            env = dict(os.environ, ANOTE_DATA=str(target))
            subprocess.run([sys.executable,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), "embed.py"), "--full"],
                           env=env, timeout=900)
        except Exception:  # noqa: BLE001
            pass
    print(f"✓ 迁移完成: {src} → {target}（文件 {n_before} 个；源未删除=双保险）")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
