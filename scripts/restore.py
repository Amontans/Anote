#!/usr/bin/env python3
"""anote restore —— 备份恢复/演练（v1.8 P0）。

--dry-run: 校验 checksum + 列出内容（不落盘）
--force: 解压到数据目录（或 --to 指定目标）
接口声明（契约）:
    输入: <备份文件> [--dry-run] [--force] [--to 目录] [--key 口令]
    输出: stdout=校验/恢复报告；退出码 0/1
    副作用: --force 时写文件
"""
import os
import subprocess
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print("用法: anote restore <备份文件> [--dry-run] [--force] [--to 目录] [--key 口令]")
        return 1
    path = Path(os.path.expanduser(args[0]))
    dry = "--dry-run" in args
    force = "--force" in args
    to = None
    if "--to" in args:
        to = Path(os.path.expanduser(args[args.index("--to") + 1]))
    key = None
    if "--key" in args:
        key = args[args.index("--key") + 1]

    if not path.exists():
        print(f"✗ 备份不存在: {path}")
        return 1

    # 解密（.enc）
    if path.name.endswith(".enc"):
        if not key:
            import getpass
            key = getpass.getpass("加密口令: ")
        plain = path.with_suffix("")  # 去掉 .enc
        subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2",
                        "-pass", f"pass:{key}", "-in", str(path), "-out", str(plain)], check=True)
        path = plain

    # 校验和
    sha = Path(str(path) + ".sha256")
    if not sha.exists():
        sha = path.parent / (path.name.replace(".tar.gz", "") + ".sha256")
        if not sha.exists():
            sha = path.parent / (path.stem + ".sha256")
    if sha.exists():
        expected = sha.read_text(encoding="utf-8").split()[0]
        import hashlib
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        ok = h.hexdigest() == expected
        print(f"校验和: {'✓ 一致' if ok else '✗ 不一致！'}（{h.hexdigest()[:12]}…）")
        if not ok:
            return 1
    else:
        print("（无 .sha256，跳过校验）")

    # dry-run：列出内容
    with tarfile.open(path, "r:gz") as tf:
        members = tf.getmembers()
        total = sum(m.size for m in members) / 1024 / 1024
        print(f"内容: {len(members)} 项，约 {total:.1f} MB")
        if dry:
            for m in members[:15]:
                print(f"  {'📁' if m.isdir() else '📄'} {m.name}")
            print("  …（--dry-run 未落盘；--force 执行还原）")
            return 0

    # 还原
    target = to or Config.load().data_dir
    if not force:
        print(f"（未加 --force，仅预览。加 --force 还原到 {target}）")
        return 0
    if not dry:
        target = Path(target)
        with tarfile.open(path, "r:gz") as tf:
            safe = []
            for m in tf.getmembers():
                member_name = m.name.replace("\\", "/")
                if member_name.startswith("/") or ".." in Path(member_name).parts:
                    print(f"✗ 拒绝不安全的备份成员: {m.name}")
                    return 1
                # 只还原普通文件与目录，跳过链接/设备
                if not (m.isfile() or m.isdir()):
                    print(f"（跳过特殊文件: {m.name}）")
                    continue
                # 剥离备份顶层目录（arcname=数据目录名）
                parts = m.name.split("/", 1)
                if len(parts) > 1:
                    m.name = parts[1]
                elif m.isdir():
                    m.name = "."
                safe.append(m)
            tf.extractall(target, members=safe)
        print(f"✓ 已还原到 {target}（请运行 anote check 验证）")
    return 0

if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
