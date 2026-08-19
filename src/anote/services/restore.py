"""备份恢复领域服务：校验、预览、安全还原（防路径穿越）。"""
from __future__ import annotations

import hashlib
import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RestoreReport:
    ok: bool
    message: str
    extracted_to: Path | None = None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _decrypt(enc_path: Path, key: str | None) -> Path:
    if not key:
        import getpass
        key = getpass.getpass("加密口令: ")
    plain = enc_path.with_suffix("")  # 去掉 .enc
    subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2",
                    "-pass", f"pass:{key}", "-in", str(enc_path),
                    "-out", str(plain)], check=True)
    return plain


def _sidecar_for(path: Path) -> Path | None:
    candidates = [
        Path(str(path) + ".sha256"),
        path.parent / (path.name.replace(".tar.gz", "") + ".sha256"),
        path.parent / (path.stem + ".sha256"),
    ]
    return next((p for p in candidates if p.exists()), None)


def verify_checksum(path: Path) -> tuple[bool, str, str | None]:
    """→ (ok, 实际摘要, 期望摘要)。"""
    sidecar = _sidecar_for(path)
    if sidecar is None:
        return True, sha256_file(path), None
    expected = sidecar.read_text(encoding="utf-8").split()[0]
    actual = sha256_file(path)
    return actual == expected, actual, expected


def inspect_archive(path: Path) -> tuple[list[tarfile.TarInfo], float]:
    with tarfile.open(path, "r:gz") as tf:
        members = tf.getmembers()
        total = sum(m.size for m in members) / 1024 / 1024
        return members, total


def _safe_member(m: tarfile.TarInfo) -> str | None:
    """返回错误信息；安全返回 None。"""
    name = m.name.replace("\\", "/")
    if name.startswith("/") or ".." in Path(name).parts:
        return f"拒绝不安全的备份成员: {m.name}"
    if not (m.isfile() or m.isdir()):
        return f"跳过特殊文件: {m.name}"
    return None


def extract_archive(path: Path, target: Path) -> tuple[bool, str]:
    """安全解包：拒绝路径穿越/特殊文件，剥离顶层数据目录。"""
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "r:gz") as tf:
        safe = []
        for m in tf.getmembers():
            err = _safe_member(m)
            if err:
                if err.startswith("拒绝"):
                    return False, err
                continue
            parts = m.name.split("/", 1)
            if len(parts) > 1:
                m.name = parts[1]
            elif m.isdir():
                m.name = "."
            safe.append(m)
        tf.extractall(target, members=safe)
    return True, "ok"


def restore_backup(path: Path, target: Path | None, *,
                   dry_run: bool = False, force: bool = False,
                   key: str | None = None) -> RestoreReport:
    """校验/预览/还原主流程。"""
    path = Path(path)
    if not path.exists():
        return RestoreReport(False, f"备份不存在: {path}")

    if path.name.endswith(".enc"):
        try:
            path = _decrypt(path, key)
        except subprocess.CalledProcessError:
            return RestoreReport(False, "解密失败（口令错误或 openssl 缺失）")

    ok, actual, expected = verify_checksum(path)
    if not ok:
        return RestoreReport(False, f"校验和不一致！实际 {actual[:12]}… 期望 {expected[:12]}…")
    checksum_msg = "校验和: ✓ 一致" if expected else "（无 .sha256，跳过校验）"

    members, total = inspect_archive(path)
    if dry_run:
        lines = [checksum_msg, f"内容: {len(members)} 项，约 {total:.1f} MB"]
        for m in members[:15]:
            lines.append(f"  {'📁' if m.isdir() else '📄'} {m.name}")
        lines.append("  …（--dry-run 未落盘；--force 执行还原）")
        return RestoreReport(True, "\n".join(lines))

    target = Path(target) if target else None
    if not force or target is None:
        return RestoreReport(True, f"{checksum_msg}\n（未加 --force，仅预览。加 --force 还原）")
    ok_extract, err = extract_archive(path, target)
    if not ok_extract:
        return RestoreReport(False, err)
    return RestoreReport(True, f"✓ 已还原到 {target}（请运行 anote check 验证）",
                         extracted_to=target)
