"""CLI 公共设施：统一入口守卫 / 错误格式化 / 模块契约约定。

用法（每个 scripts/*.py 薄适配器）:
    if __name__ == "__main__":
        sys.exit(cli_run(main))      # cli_run = cli.run

契约声明（每个模块 docstring 必须包含）:
    输入: argv（见 argparse）；配置经 anote.core.Config（ANOTE_DATA 可覆盖）
    输出: stdout=结果；stderr=错误；退出码 0 成功 / 1 失败
    副作用: （列出写入的文件/调用）
"""
from __future__ import annotations

import sys
import traceback
from typing import Callable, TypeVar, Union

from .core import Result, setup_logging

T = TypeVar("T")


def run(entry: Callable[[], Union[Result, int, None]], name: str = "") -> int:
    """统一入口守卫：捕获一切异常 → 单行可读错误（类型+位置）→ 退出码 1。

    - 不打印长 traceback（细节进日志 <数据根>/.anote/logs/anote.log）
    - Result 结果自动按 stdout/stderr 约定输出
    """
    logger = setup_logging(f"anote.cli.{name}" if name else "anote.cli")
    try:
        r = entry()
        if isinstance(r, Result):
            if r.stdout:
                print(r.stdout)
            if r.stderr and not r.ok:
                print(f"✗ {r.stderr}", file=sys.stderr)
            return 0 if r.ok else (r.exit_code or 1)
        return 0 if r is None else int(r)
    except Exception as e:  # noqa: BLE001
        logger.error("命令失败", exc_info=True)
        print(f"✗ 错误 [{e.__class__.__name__}]: {e}", file=sys.stderr)
        return 1


def err(msg: str, code: int = 1) -> Result:
    """构造失败结果（简短错误，不抛异常）。"""
    return Result.failure(msg, code)
