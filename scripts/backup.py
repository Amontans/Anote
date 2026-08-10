#!/usr/bin/env python3
"""anote backup-create —— 加密/校验备份（v1.8 P0：数据安全命脉）。

输出: ~/Documents/anote-backups/anote-backup-<日期>.tar.gz（+ .sha256；--encrypt 时 .enc）
排除: .venv/.semantic（可重建）；默认含 .git（完整历史）
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
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402

EXCLUDE = {".venv", ".semantic", "__pycache__"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    args = sys.argv[1:]
    out_dir = Path(os.path.expanduser("~/Documents/anote-backups"))
    encrypt = "--encrypt" in args
    with_git = "--no-git" not in args
    if "--out" in args:
        out_dir = Path(os.path.expanduser(args[args.index("--out") + 1]))

    data = Path(Config.load().data_dir)
    if not data.is_dir():
        print(f"✗ 数据目录不存在: {data}")
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / f"anote-backup-{date.today().isoformat()}"
    tar = Path(str(base) + ".tar.gz")

    def filt(ti):
        name = Path(ti.name)
        if any(part in EXCLUDE for part in name.parts):
            return None
        if not with_git and ".git" in name.parts:
            return None
        return ti

    with tarfile.open(tar, "w:gz") as tf:
        tf.add(data, arcname=data.name, filter=filt)
    digest = sha256(tar)
    (Path(str(base) + ".sha256")).write_text(f"{digest}  {tar.name}\n", encoding="utf-8")

    final = tar
    if encrypt:
        key = os.environ.get("ANOTE_BACKUP_KEY")
        if not key:
            import getpass
            key = getpass.getpass("加密口令: ")
        enc = Path(str(base) + ".tar.gz.enc")
        subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-pass", f"pass:{key}",
                        "-in", str(tar), "-out", str(enc)], check=True)
        tar.unlink()  # 删除明文
        final = enc
        (Path(str(base) + ".sha256")).write_text(f"{digest}  {final.name}\n", encoding="utf-8")

    size = final.stat().st_size / 1024 / 1024
    print(f"✓ 备份完成: {final}（{size:.1f} MB）")
    print(f"  SHA256: {digest[:16]}…")
    print(f"  （还原: anote restore {final} --dry-run 演练 / --force 执行）")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
