#!/usr/bin/env python3
"""Anote 唯一配置源（bash 与 python 共用 ~/.config/anote/config，KEY=VALUE）。

所有脚本的默认数据目录从此处读取——data_dir 可被 TUI 设置页更改。
bash 侧解析:  $(grep -E '^data_dir=' ~/.config/anote/config | cut -d= -f2-)
"""
import os

CONFIG_PATH = os.path.expanduser("~/.config/anote/config")

DEFAULTS = {
    "data_dir": os.path.expanduser("~/Documents/Anote"),
    "editor": "code",
    "lang": "zh",
    "semantic_model": "BAAI/bge-small-zh-v1.5",
    "onboarded": "false",
}

# 编辑器可选值（TUI 设置页 Select 用）
EDITOR_CHOICES = ["code", "vim", "nvim", "emacs", "gedit", "nano"]


def load():
    """读取配置，缺项用默认值。文件不存在返回默认。"""
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    cfg[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return cfg


def get(key, default=None):
    return load().get(key, default)


def data_dir():
    """返回展开后的数据目录：优先 ANOTE_DATA 环境变量（测试/临时覆盖），再读配置。"""
    env = os.environ.get("ANOTE_DATA")
    if env:
        return os.path.expanduser(env)
    return os.path.expanduser(load().get("data_dir", DEFAULTS["data_dir"]))


def set(key, value):
    """写回配置（保留其他键）。"""
    cfg = load()
    cfg[key] = str(value)
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        for k, v in cfg.items():
            f.write(f"{k}={v}\n")


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "set":
        set(sys.argv[2], sys.argv[3])
    else:
        for k, v in load().items():
            print(f"{k}={v}")
