#!/usr/bin/env python3
"""AnoteContext：TUI 各部件共享的"数据总线"。

所有屏幕/部件只依赖本类读取配置、读取数据、调用脚本——不直接碰文件系统细节。
未来新增部件（队列表格、笔记树等）一律经此访问，保证接口单一、可测。
"""
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import anote_config as cfg  # noqa: E402

from textual.message import Message  # noqa: E402

from anote.core import PROJECT_ROOT  # noqa: E402
from anote.services import NotesService, QueueService  # noqa: E402


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
        """保存配置。data_dir 不能直接改，必须走 migrate。"""
        if key == "data_dir":
            raise ValueError("data_dir 不能直接修改，请使用迁移向导")
        cfg.set(key, value)
        self.reload()

    # ---- 脚本调用（薄壳核心）----
    def script_path(self, name):
        return os.path.join(PROJECT_ROOT, "scripts", name)

    async def run_script_async(self, name, *args, timeout=1800):
        """异步脚本调用（TUI 内不阻塞界面，迁移等长任务用）。"""
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, self.script_path(name), *args,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out, err = await asyncio.wait_for(proc.communicate(), timeout)
            return RunResult(out.decode("utf-8", "ignore"), err.decode("utf-8", "ignore"), proc.returncode)
        except asyncio.TimeoutError:
            return RunResult("", "超时", 124)
        except FileNotFoundError:
            return RunResult("", f"脚本不存在: {name}", 127)

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

    # ---- 状态查询（Home 仪表盘用；经 services，不重复解析）----
    def note_count(self):
        return len(NotesService(Path(self.data_dir)).scan())

    def queue_counts(self):
        return QueueService(Path(self.data_dir)).counts()

    def semantic_ready(self):
        return os.path.isdir(os.path.join(self.data_dir, ".semantic"))

    def last_review(self):
        d = os.path.join(self.data_dir, "memory", "reviews")
        if not os.path.isdir(d):
            return "无"
        files = [f for f in os.listdir(d) if f.endswith(".md")]
        return max(files, key=lambda f: os.path.getmtime(os.path.join(d, f))) if files else "无"


    # ---- 统计与迁移 ----
    def stats(self):
        """统计各类文件数（anote stats --json）。"""
        r = self.run_script("stats.py", "--json", timeout=30)
        if not r.ok:
            return {}
        try:
            return json.loads(r.stdout)
        except Exception:  # noqa: BLE001
            return {}

    def migrate_data_dir(self, target, with_env=True):
        """迁移数据目录（含 .git），返回 RunResult。"""
        args = ["--to", target, "--force"]
        if with_env:
            args.append("--with-env")
        return self.run_script("migrate.py", *args, timeout=1800)


    # ---- 全文检索（rg）----
    def rg(self, pattern, max_results=50):
        """rg 全文检索，返回 [(path, lineno, snippet)]。"""
        cmd = ["rg", "-n", "-i", pattern, self.data_dir,
               "-g", "*.tex", "-g", "*.md",
               "-g", "!00-index.tex", "-g", "!README.md", "--max-count", "1"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        except FileNotFoundError:
            return []
        results = []
        for line in proc.stdout.splitlines():
            p, _, rest = line.partition(":")
            if not rest:
                continue
            ln, _, text = rest.partition(":")
            results.append((p, ln, text[:120].strip()))
            if len(results) >= max_results:
                break
        return results


    # ---- AI 问答（经 Pi 代理 → DeepSeek）----
    def _pi_bin(self):
        import shutil
        return shutil.which("pi") or os.path.expanduser("~/.bun/bin/pi")

    def run_pi(self, prompt, timeout=180):
        """调用 Pi（-p 打印模式）回答问题。Pi 会自动加载 Anote 规则/记忆/技能。"""
        try:
            proc = subprocess.run([self._pi_bin(), "-p", prompt],
                                  capture_output=True, text=True, timeout=timeout)
            return RunResult(proc.stdout.strip(), proc.stderr.strip(), proc.returncode)
        except subprocess.TimeoutExpired:
            return RunResult("", "Pi 响应超时", 124)
        except FileNotFoundError:
            return RunResult("", "未找到 pi 命令", 127)

    async def run_pi_async(self, prompt, timeout=180):
        """异步调用 Pi（TUI 内不阻塞界面）。"""
        try:
            proc = await asyncio.create_subprocess_exec(
                self._pi_bin(), "-p", prompt,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            out, err = await asyncio.wait_for(proc.communicate(), timeout)
            return RunResult(out.decode("utf-8", "ignore").strip(),
                             err.decode("utf-8", "ignore").strip(), proc.returncode)
        except asyncio.TimeoutError:
            return RunResult("", "Pi 响应超时", 124)
        except FileNotFoundError:
            return RunResult("", "未找到 pi 命令", 127)
