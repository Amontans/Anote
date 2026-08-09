"""Anote 业务逻辑核心（现代化改造：模块化/类型化/配置单点/结果模式）。

分层：CLI/TUI（表现层）→ src/anote 包（业务层）→ 数据目录（数据层）。
"""
from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

# src/anote/core.py → src → 项目根
SRC_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SRC_DIR.parent
CONFIG_PATH = Path("~/.config/anote/config").expanduser()
LOG_PATH = Path("~/.config/anote/logs/anote.log").expanduser()
DEFAULT_DATA_DIR = Path("~/Documents/Anote").expanduser()


@dataclass
class Config:
    """唯一配置模型：单点读写，支持 ANOTE_DATA 环境覆盖（测试/临时）。"""

    data_dir: Path = DEFAULT_DATA_DIR
    editor: str = "code"
    lang: str = "zh"
    semantic_model: str = "BAAI/bge-small-zh-v1.5"
    onboarded: str = "false"

    @classmethod
    def load(cls) -> "Config":
        cfg = cls()
        env = os.environ.get("ANOTE_DATA")
        if CONFIG_PATH.exists():
            for line in CONFIG_PATH.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    if hasattr(cfg, k.strip()):
                        setattr(cfg, k.strip(), v.strip())
        cfg.data_dir = Path(env).expanduser() if env else Path(str(cfg.data_dir)).expanduser()
        return cfg

    def save(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            "\n".join(f"{k}={getattr(self, k)}" for k in self.__dataclass_fields__) + "\n",
            encoding="utf-8")

    def set(self, key: str, value: str) -> None:
        if hasattr(self, key):
            setattr(self, key, value)
            self.save()


@dataclass
class Result:
    """统一结果模式：所有命令/服务返回它，避免散乱的错误处理。"""

    ok: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0

    @classmethod
    def success(cls, stdout: str = "") -> "Result":
        return cls(True, stdout=stdout)

    @classmethod
    def failure(cls, stderr: str, code: int = 1) -> "Result":
        return cls(False, stderr=stderr, exit_code=code)

    @property
    def tail(self) -> str:
        text = self.stdout.strip() or self.stderr.strip()
        lines = text.splitlines()
        return lines[-1] if lines else ""


def setup_logging(name: str = "anote") -> logging.Logger:
    """标准日志：滚动文件 ~/.config/anote/logs/anote.log + 控制台。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(fh)
    return logger


def ensure_import() -> None:
    """让 scripts/*.py（薄适配器）能 import anote 包。"""
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
