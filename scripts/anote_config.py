#!/usr/bin/env python3
"""配置兼容层（shim）：统一到 anote.core.Config 单一实现（DRY）。

配置位置: <数据根>/.anote/config；ANOTE_DATA 决定数据根。
旧脚本 `from anote_config import data_dir` 继续可用；新代码直接用 anote.core.Config。
接口声明（契约）:
    输入: argv（set 键 值 / 无参数=打印全部）
    输出: stdout=配置表或提示；stderr=错误；退出码 0/1
    副作用: set 时写 <数据根>/.anote/config
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402


def load() -> dict:
    c = Config.load()
    return {k: str(getattr(c, k)) for k in c.__dataclass_fields__}


def get(key: str, default=None):
    return getattr(Config.load(), key, default)


def data_dir() -> str:
    return str(Config.load().data_dir)


def set(key: str, value: str) -> None:
    Config.load().set(key, value)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "set" and len(sys.argv) < 4:
        print("用法: anote config set <键> <值>", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) >= 3 and sys.argv[1] == "set":
        try:
            set(sys.argv[2], sys.argv[3])
            print(f"✓ 已保存: {sys.argv[2]}={sys.argv[3]}")
        except (ValueError, OSError) as e:
            print(f"✗ 配置保存失败: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        for k, v in load().items():
            print(f"{k}={v}")


if __name__ == "__main__":
    sys.exit(main())
