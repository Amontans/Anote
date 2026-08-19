"""Anote 业务逻辑核心：模块化/类型化/配置单点/结果模式。

可移植性约定（v1.15+）：
- 唯一用户数据根由 `ANOTE_DATA`（最高优先）、`~/.config/anote/config` 中的
  `data_dir` 定位指针、默认 `~/Documents/Anote` 依次解析；
- 配置、日志、外部 MCP 注册、迁移日志、默认备份/导出，全部位于数据根下的 `.anote/`；
- `~/.config/anote/config` 只保留一行 `data_dir=` 指针用于发现非默认数据根，
  不承载其他用户数据；项目仓库可直接上传 GitHub。
"""
from __future__ import annotations

import logging
import os
import shutil
import sys
from dataclasses import dataclass, fields
from logging.handlers import RotatingFileHandler
from pathlib import Path

# src/anote/core.py → src → 项目根
SRC_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SRC_DIR.parent
DEFAULT_DATA_DIR = Path("~/Documents/Anote").expanduser()
LEGACY_CONFIG_PATH = Path("~/.config/anote/config").expanduser()
APP_DIR = ".anote"


# ---------------------------------------------------------------------------
# 路径解析（数据根是唯一真相源；~/.config 仅保留一行定位指针）
# ---------------------------------------------------------------------------

def _legacy_data_dir() -> Path | None:
    """读取数据根定位指针：~/.config/anote/config 中的 data_dir。"""
    if not LEGACY_CONFIG_PATH.exists():
        return None
    try:
        for line in LEGACY_CONFIG_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                if k.strip() == "data_dir":
                    return Path(v.strip()).expanduser()
    except OSError:
        return None
    return None


def resolve_data_dir(use_legacy: bool = True) -> Path:
    """解析数据根：ANOTE_DATA > 定位指针 > 默认目录。"""
    env = os.environ.get("ANOTE_DATA")
    if env:
        return Path(env).expanduser()
    if use_legacy:
        legacy = _legacy_data_dir()
        if legacy is not None:
            return legacy
    return DEFAULT_DATA_DIR


def app_dir_for(data_dir: Path) -> Path:
    return Path(data_dir) / APP_DIR


def config_path_for(data_dir: Path) -> Path:
    return app_dir_for(data_dir) / "config"


def log_path_for(data_dir: Path) -> Path:
    return app_dir_for(data_dir) / "logs" / "anote.log"


def external_config_path_for(data_dir: Path) -> Path:
    return app_dir_for(data_dir) / "external.json"


def migration_log_path_for(data_dir: Path) -> Path:
    return app_dir_for(data_dir) / "migration.log"


def backup_dir_for(data_dir: Path) -> Path:
    return app_dir_for(data_dir) / "backups"


def export_dir_for(data_dir: Path) -> Path:
    return app_dir_for(data_dir) / "exports"


def update_data_dir_pointer(data_dir: Path, force: bool = False) -> None:
    """写/更新数据根定位指针（~/.config/anote/config，仅 data_dir 一行）。

    测试/临时环境（ANOTE_DATA 已设置）默认不写，避免污染真实 HOME。
    """
    if not force and os.environ.get("ANOTE_DATA"):
        return
    try:
        LEGACY_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        LEGACY_CONFIG_PATH.write_text(f"data_dir={Path(data_dir).expanduser()}\n", encoding="utf-8")
    except OSError:
        pass


def _migrate_legacy_config(data_dir: Path) -> None:
    """旧版完整配置 → <数据根>/.anote/config（幂等）；旧文件改为纯定位指针。"""
    if not LEGACY_CONFIG_PATH.exists():
        return
    target = config_path_for(data_dir)
    try:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(LEGACY_CONFIG_PATH, target)
        # 完整配置已进入数据根；旧文件只保留 data_dir 指针
        update_data_dir_pointer(data_dir)
    except OSError:
        pass


@dataclass
class Config:
    """唯一配置模型：配置文件位于 <数据根>/.anote/config。

    data_dir 由 ANOTE_DATA 或默认目录决定，不信任配置文件中的旧字段；
    修改 data_dir 必须走 anote migrate --to。
    """

    data_dir: Path = DEFAULT_DATA_DIR
    editor: str = "code"
    lang: str = "zh"
    semantic_model: str = "BAAI/bge-small-zh-v1.5"
    onboarded: str = "false"
    ai_provider: str = "pi"       # AI 层：默认经 Pi 代理（不直连模型）
    pi_bin: str = ""              # 留空时自动在 PATH / ~/.bun/bin 查找
    theme: str = "textual-dark"   # TUI 主题（Textual 内置）
    reader: str = ""              # 阅读器（留空时按扩展名自动选择）

    @classmethod
    def load(cls) -> "Config":
        env = os.environ.get("ANOTE_DATA")
        data_dir = Path(env).expanduser() if env else resolve_data_dir()
        # 仅非测试/非 env 覆盖时迁移旧完整配置；ANOTE_DATA 是隔离测试的硬边界
        if not env:
            _migrate_legacy_config(data_dir)

        cfg = cls()
        cfg.data_dir = data_dir
        path = config_path_for(data_dir)
        # 新配置不存在时，兼容读取旧配置（例如数据根只读、无法迁移的场景）
        source = path if path.exists() else (LEGACY_CONFIG_PATH if LEGACY_CONFIG_PATH.exists() else None)
        if source is not None:
            try:
                for line in source.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, _, v = line.partition("=")
                        k = k.strip()
                        # data_dir 一律以解析结果为准，不读配置文件里的旧值
                        if k != "data_dir" and hasattr(cfg, k):
                            setattr(cfg, k, v.strip())
            except OSError:
                pass
        return cfg

    def save(self) -> None:
        path = config_path_for(self.data_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(f"{f.name}={getattr(self, f.name)}"
                      for f in fields(self)) + "\n",
            encoding="utf-8")
        # 让系统以后能发现这个数据根（非默认路径时尤其重要）
        update_data_dir_pointer(self.data_dir)

    def set(self, key: str, value: str) -> bool:
        if key == "data_dir":
            raise ValueError("data_dir 不能直接修改，请使用 anote migrate --to <新路径>")
        if not hasattr(self, key):
            raise ValueError(f"未知配置键: {key}")
        setattr(self, key, value)
        self.save()
        return True


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
    """标准日志：<数据根>/.anote/logs/anote.log + 控制台兜底。

    日志目录不可写时降级为 stderr，绝不让日志失败拖垮命令。
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_ok = False
    try:
        path = log_path_for(Config.load().data_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        file_ok = True
    except Exception:  # noqa: BLE001
        file_ok = False
    if not file_ok:
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    return logger


def ensure_import() -> None:
    """让 scripts/*.py（薄适配器）能 import anote 包。"""
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))


def ai_ask(prompt: str, timeout: int = 180) -> Result:
    """统一 AI 入口：经 Config.ai_provider 调用（当前唯一实现=pi 代理）。"""
    import subprocess
    cfg = Config.load()
    if cfg.ai_provider == "pi":
        pi_bin = cfg.pi_bin or shutil.which("pi") or str(Path.home() / ".bun/bin/pi")
        try:
            proc = subprocess.run([pi_bin, "-p", prompt], capture_output=True,
                                  text=True, timeout=timeout)
            return Result(proc.returncode == 0, stdout=proc.stdout.strip(),
                          stderr=proc.stderr.strip(), exit_code=proc.returncode)
        except subprocess.TimeoutExpired:
            return Result.failure("AI 响应超时", 124)
        except FileNotFoundError:
            return Result.failure(f"未找到 pi 命令: {pi_bin}", 127)
    return Result.failure(f"未支持的 ai_provider: {cfg.ai_provider}")
