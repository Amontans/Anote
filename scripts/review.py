#!/usr/bin/env python3
"""知识回顾生成器：扫描 ~/Documents/Anote 中新笔记，生成周/月回顾草稿（Markdown）。

用法:
  review.py                 # 默认最近 7 天
  review.py --days 30       # 月度回顾
  review.py --since "2026-08-01"   # 指定起始日期
  review.py --out 路径.md   # 指定输出
"""
import argparse
import datetime
import os
import re
import subprocess
import sys

DATA = os.path.expanduser("~/Documents/Anote")


def git_changed_since(since_dt):
    """用 git log 找 since 之后改动的 .tex/.md 文件。"""
    try:
        out = subprocess.run(
            ["git", "-C", DATA, "log", "--since", since_dt.strftime("%Y-%m-%d 00:00"),
             "--name-only", "--pretty=format:"],
            capture_output=True, text=True, timeout=15).stdout
        files = sorted({l.strip() for l in out.splitlines()
                        if l.strip().endswith((".tex", ".md"))})
        return [f for f in files if f.startswith(("src/", "memory/"))]
    except Exception:  # noqa: BLE001
        return []


def files_mtime_since(since_dt):
    """mtime 兜底扫描。"""
    hits = []
    for root, _, files in os.walk(os.path.join(DATA, "src")):
        for f in files:
            if f.endswith((".tex", ".md")):
                p = os.path.join(root, f)
                if datetime.datetime.fromtimestamp(os.path.getmtime(p)) >= since_dt:
                    hits.append(os.path.relpath(p, DATA))
    return sorted(hits)


def extract_title(path):
    try:
        src = open(path, encoding="utf-8").read()
        m = re.search(r"\\title\{([^}]+)\}", src) or re.search(r"^# (.+)$", src, re.M)
        return m.group(1).strip() if m else os.path.basename(path)
    except Exception:  # noqa: BLE001
        return os.path.basename(path)


def week_label():
    d = datetime.date.today()
    return f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--since")
    ap.add_argument("--out")
    a = ap.parse_args()

    since_dt = (datetime.datetime.strptime(a.since, "%Y-%m-%d")
                if a.since else datetime.datetime.now() - datetime.timedelta(days=a.days))
    changed = git_changed_since(since_dt) or files_mtime_since(since_dt)
    papers = [f for f in changed if f.startswith("src/papers/")]
    others = [f for f in changed if not f.startswith("src/papers/")]

    label = week_label() if a.days <= 14 else since_dt.strftime("%Y-%m")
    out_path = (os.path.expanduser(a.out)
                if a.out else os.path.join(DATA, "memory", "reviews", f"review-{label}.md"))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    lines = [f"# 知识回顾 · {label}", "", "## 本周期活动"]
    if changed:
        for f in changed:
            lines.append(f"- `{f}` —— 《{extract_title(os.path.join(DATA, f))}》")
    else:
        lines.append("- （本周期无新笔记）")
    lines += [f"", f"## 新读论文（{len(papers)} 篇，列表见上）", "",
              "## 关键洞见（AI 阅读后提炼，写入 insights.md）", "- ", "",
              "## 新概念（登记入 concepts.md）", "- ", "",
              "## 开放问题更新（open-questions.md）", "- ", "",
              "## 路线图审视（更新 roadmap.md）", "- 本季度目标进度：", "- 需要调整的方向/优先级：", "",
              "## 下周计划", "- ", ""]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"回顾草稿已生成: {out_path}")
    print(f"本周期改动文件 {len(changed)} 个（论文 {len(papers)} 篇）")


if __name__ == "__main__":
    main()
