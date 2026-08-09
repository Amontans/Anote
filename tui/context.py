#!/usr/bin/env python3
"""AnoteContext：TUI 各部件共享的"数据总线"。

所有屏幕/部件只依赖本类读取配置、读取数据、调用脚本——不直接碰文件系统细节。
未来新增部件（队列表格、笔记树等）一律经此访问，保证接口单一、可测。
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import anote_config as cfg  # noqa: E402

from textual.message import Message  # noqa: E402

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ConfigChanged(Message):
    """设置变更事件：设置页保存后广播，相关部件监听刷新。"""


class RunResult:
    def __init__(self, stdout="", stderr="", exit_code=0):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code

    @property
    def ok(self):
        return self.exit_code == 0

    @property
    def tail(self):
        text = self.stdout.strip() or self.stderr.strip()
        lines = text.splitlines()
        return lines[-1] if lines else ""


class AnoteContext:
    """数据总线：config + 数据文件 + 脚本调用（单一依赖点）"""

    def __init__(self):
        self._cfg = cfg.load()

    # ---- 配置 ----
    @property
    def data_dir(self):
        return cfg.data_dir()

    @property
    def editor(self):
        return cfg.get("editor", "code")

    @property
    def lang(self):
        return cfg.get("lang", "zh")

    @property
    def semantic_model(self):
        return cfg.get("semantic_model", "BAAI/bge-small-zh-v1.5")

    @property
    def config(self):
        return cfg.load()

    def reload(self):
        self._cfg = cfg.load()

    def set_config(self, key, value):
        cfg.set(key, value)
        self.reload()

    # ---- 脚本调用（薄壳核心）----
    def script_path(self, name):
        return os.path.join(PROJECT_ROOT, "scripts", name)

    def run_script(self, name, *args, timeout=120):
        try:
            proc = subprocess.run(
                [sys.executable, self.script_path(name), *args],
                capture_output=True, text=True, timeout=timeout)
            return RunResult(proc.stdout, proc.stderr, proc.returncode)
        except subprocess.TimeoutExpired:
            return RunResult("", "超时", 124)
        except FileNotFoundError:
            return RunResult("", f"脚本不存在: {name}", 127)

    # ---- 数据访问（契约化，路径防逃逸）----
    def safe_rel(self, rel):
        base = os.path.realpath(self.data_dir)
        p = os.path.realpath(os.path.join(self.data_dir, rel))
        if p != base and not p.startswith(base + os.sep):
            raise ValueError(f"非法路径: {rel}")
        return rel

    def read_data(self, rel):
        self.safe_rel(rel)
        with open(os.path.join(self.data_dir, rel), encoding="utf-8") as f:
            return f.read()

    def write_data(self, rel, content):
        self.safe_rel(rel)
        with open(os.path.join(self.data_dir, rel), "w", encoding="utf-8") as f:
            f.write(content)

    # ---- 状态查询（Home 仪表盘用）----
    def note_count(self):
        n = 0
        for root, _, files in os.walk(os.path.join(self.data_dir, "src")):
            n += sum(1 for f in files if f.endswith((".tex", ".md")))
        return n

    def queue_counts(self):
        try:
            q = self.read_data("queue.md")
        except Exception:  # noqa: BLE001
            return {"📥": 0, "📖": 0, "✅": 0, "🗄": 0}
        return {k: q.count(k) for k in ("📥", "📖", "✅", "🗄")}

    def semantic_ready(self):
        return os.path.isdir(os.path.join(self.data_dir, ".semantic"))

    def last_review(self):
        d = os.path.join(self.data_dir, "memory", "reviews")
        if not os.path.isdir(d):
            return "无"
        files = [f for f in os.listdir(d) if f.endswith(".md")]
        return max(files, key=lambda f: os.path.getmtime(os.path.join(d, f))) if files else "无"
