#!/usr/bin/env python3
"""anote lint —— LaTeX 语法/风格检查（chktex 包装，零依赖）。

接口声明（契约）:
    输入: <tex文件>（相对数据目录）
    输出: stdout=警告行；退出码 0（无错误）
    副作用: 无
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("用法: anote lint <tex文件>（如 src/数学/代数/环论基础.tex）")
        return 1
    data = Path(Config.load().data_dir)
    p = data / args[0]
    if not p.exists():
        print(f"✗ 不存在: {p}")
        return 1
    r = subprocess.run(["chktex", "-q", "-f", "%f:%l:%c: %m", str(p)],
                       capture_output=True, text=True)
    out = r.stdout.strip()
    if not out:
        print("✓ 无警告（chktex）")
        return 0
    print(f"⚠️ chktex 检查 {p.name}：")
    print(out)
    print("\n提示: 需补全/跳转可用 texlab（sudo pacman -S texlab，编辑器 LSP）")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
