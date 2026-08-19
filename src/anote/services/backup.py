"""备份领域服务：tar.gz + SHA256 校验（可选 AES-256 加密）。

默认输出 `<数据根>/.anote/backups/`；备份包含 `.anote/config` 与
`external.json`，排除日志/备份/导出/预览/迁移日志及 .venv/.semantic。
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import tarfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..core import backup_dir_for

EXCLUDE_PARTS = {".venv", ".semantic", "__pycache__"}
EXCLUDE_REL = {".anote/logs", ".anote/backups", ".anote/exports",
               ".anote/previews", ".anote/migration.log"}


@dataclass
class BackupResult:
    path: Path
    digest: str
    size_mb: float


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _excluded_rel(parts: tuple) -> bool:
    if any(part in EXCLUDE_PARTS for part in parts):
        return True
    if ".anote" in parts:
        rel = Path(*parts[parts.index(".anote"):])
        if str(rel) in EXCLUDE_REL or any(rel.is_relative_to(Path(x)) for x in EXCLUDE_REL):
            return True
    return False


def create_backup(data_dir: Path, out_dir: Path | None = None, *,
                  encrypt: bool = False, with_git: bool = True,
                  key: str | None = None) -> BackupResult:
    """创建备份；返回 (路径, 摘要)。"""
    data = Path(data_dir).expanduser()
    if not data.is_dir():
        raise FileNotFoundError(f"数据目录不存在: {data}")
    out = Path(out_dir).expanduser() if out_dir else backup_dir_for(data)
    out.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d")
    base = out / f"anote-backup-{stamp}"
    if base.with_suffix(".tar.gz").exists() or Path(str(base) + ".tar.gz.enc").exists():
        base = out / f"anote-backup-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"

    def filt(ti):
        parts = Path(ti.name).parts
        rel_parts = parts[1:] if parts and parts[0] == data.name else parts
        if _excluded_rel(rel_parts):
            return None
        if not with_git and ".git" in rel_parts:
            return None
        return ti

    tar = Path(str(base) + ".tar.gz")
    with tarfile.open(tar, "w:gz") as tf:
        tf.add(data, arcname=data.name, filter=filt)
    digest = sha256_file(tar)

    final = tar
    if encrypt:
        secret = key or os.environ.get("ANOTE_BACKUP_KEY")
        if not secret:
            import getpass
            secret = getpass.getpass("加密口令: ")
        enc = Path(str(base) + ".tar.gz.enc")
        subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-pass", f"pass:{secret}",
                        "-in", str(tar), "-out", str(enc)], check=True)
        tar.unlink()
        final = enc

    sidecar = Path(str(base) + ".sha256")
    sidecar.write_text(f"{digest}  {final.name}\n", encoding="utf-8")
    return BackupResult(final, digest, final.stat().st_size / 1024 / 1024)
