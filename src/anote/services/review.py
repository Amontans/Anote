"""回顾领域服务：周/月回顾草稿生成（git log 扫描 + 草稿模板）。"""
from __future__ import annotations

import datetime
import os
import re
import subprocess
from pathlib import Path


def git_changed_since(data: Path, since_dt: datetime.datetime) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(data), "log", "--since", since_dt.strftime("%Y-%m-%d 00:00"),
             "--name-only", "--pretty=format:"],
            capture_output=True, text=True, timeout=15).stdout
        files = sorted({l.strip() for l in out.splitlines()
                        if l.strip().endswith((".tex", ".md"))})
        return [f for f in files if f.startswith(("src/", "memory/"))]
    except Exception:  # noqa: BLE001
        return []


def files_mtime_since(data: Path, since_dt: datetime.datetime) -> list[str]:
    hits = []
    src = data / "src"
    if src.is_dir():
        for root, _, files in os.walk(src):
            for f in files:
                if f.endswith((".tex", ".md")):
                    p = Path(root) / f
                    if datetime.datetime.fromtimestamp(p.stat().st_mtime) >= since_dt:
                        hits.append(str(p.relative_to(data)))
    return sorted(hits)


def extract_title(path: Path) -> str:
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"\\title\{([^}]+)\}", src) or re.search(r"^# (.+)$", src, re.M)
        return m.group(1).strip() if m else path.name
    except Exception:  # noqa: BLE001
        return path.name


def week_label(d: datetime.date | None = None) -> str:
    d = d or datetime.date.today()
    return f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"


class ReviewService:
    def __init__(self, data_dir: Path):
        self.data = Path(data_dir)

    def generate(self, days: int = 7, out_path: Path | None = None) -> tuple[Path, int, int]:
        """生成回顾草稿 → (路径, 改动文件数, 论文数)。"""
        since = datetime.datetime.now() - datetime.timedelta(days=days)
        changed = git_changed_since(self.data, since) or files_mtime_since(self.data, since)
        papers = [f for f in changed if f.startswith("src/papers/")]
        label = week_label() if days <= 14 else since.strftime("%Y-%m")
        if out_path is None:
            out_path = self.data / "memory" / "reviews" / f"review-{label}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"# 知识回顾 · {label}", "", "## 本周期活动"]
        if changed:
            for f in changed:
                lines.append(f"- `{f}` —— 《{extract_title(self.data / f)}》")
        else:
            lines.append("- （本周期无新笔记）")
        lines += ["", f"## 新读论文（{len(papers)} 篇，列表见上）", "",
                  "## 关键洞见（AI 阅读后提炼，写入 insights.md）", "- ", "",
                  "## 新概念（登记入 concepts.md）", "- ", "",
                  "## 开放问题更新（open-questions.md）", "- ", "",
                  "## 路线图审视（更新 roadmap.md）", "- 本季度目标进度：", "- 需要调整的方向/优先级：", "",
                  "## 下周计划", "- ", ""]
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path, len(changed), len(papers)
