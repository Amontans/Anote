#!/usr/bin/env python3
"""anote backup-create —— 加密/校验备份（P0：数据安全命脉）。

默认输出: <数据根>/.anote/backups/anote-backup-<日期>.tar.gz（+ .sha256；--encrypt 时 .enc）
排除: .venv/.semantic/__pycache__ 以及 .anote 下的日志/备份/导出/迁移日志（配置会随备份走）。
接口声明（契约）:
    输入: [--out 目录] [--encrypt] [--no-git]
    输出: stdout=备份路径+校验和；退出码 0/1
    副作用: 写备份文件
"""
import hashlib
import os
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config, backup_dir_for  # noqa: E402

# 这些目录/文件是运行产物，不进入备份
EXCLUDE_PARTS = {".venv", ".semantic", "__pycache__"}
EXCLUDE_REL = {
    ".anote/logs", ".anote/backups", ".anote/exports", ".anote/previews", ".anote/migration.log",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    args = sys.argv[1:]
    data = Path(Config.load().data_dir)
    encrypt = "--encrypt" in args
    with_git = "--no-git" not in args

    out_dir = backup_dir_for(data)
    if "--out" in args:
        i = args.index("--out")
        if i + 1 < len(args):
            out_dir = Path(os.path.expanduser(args[i + 1]))

    if not data.is_dir():
        print(f"✗ 数据目录不存在: {data}")
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    base = out_dir / f"anote-backup-{stamp}"
    if base.with_suffix(".tar.gz").exists() or Path(str(base) + ".tar.gz.enc").exists():
        base = out_dir / f"anote-backup-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
    tar = Path(str(base) + ".tar.gz")

    def filt(ti):
        name = Path(ti.name)
        parts = name.parts
        # 剥掉 arcname 顶层数据目录名后判断相对路径
        rel = Path(*parts[1:]) if len(parts) > 1 and parts[0] == data.name else name
        if any(part in EXCLUDE_PARTS for part in rel.parts):
            return None
        if str(rel) in EXCLUDE_REL or any(rel.is_relative_to(Path(x)) for x in EXCLUDE_REL):
            return None
        if not with_git and ".git" in rel.parts:
            return None
        return ti

    with tarfile.open(tar, "w:gz") as tf:
        tf.add(data, arcname=data.name, filter=filt)
    digest = sha256(tar)
    sha_file = Path(str(base) + ".sha256")

    final = tar
    if encrypt:
        key = os.environ.get("ANOTE_BACKUP_KEY")
        if not key:
            import getpass
            key = getpass.getpass("加密口令: ")
        enc = Path(str(base) + ".tar.gz.enc")
        subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-pass", f"pass:{key}",
                        "-in", str(tar), "-out", str(enc)], check=True)
        tar.unlink()
        final = enc
    sha_file.write_text(f"{digest}  {final.name}\n", encoding="utf-8")

    size = final.stat().st_size / 1024 / 1024
    print(f"✓ 备份完成: {final}（{size:.1f} MB）")
    print(f"  SHA256: {digest[:16]}…")
    print(f"  （还原: anote restore {final} --dry-run 演练 / --force 执行）")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
