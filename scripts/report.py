#!/usr/bin/env python3
"""anote report —— 周报自动生成（v1.6）：本周活动 + 数据统计 + 下周建议。

来源：memory/reviews/ 最近草稿 + anote stats。
接口声明（契约）:
    输入: argv: [--out 路径]
    输出: stdout=报告路径；退出码 0/1
    副作用: 写 memory/reports/<周>.md
"""
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import StatsService  # noqa: E402


def week_label() -> str:
    d = datetime.date.today()
    return f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"


def main() -> int:
    data = Path(Config.load().data_dir)
    args = sys.argv[1:]
    out = None
    if "--out" in args:
        i = args.index("--out")
        if i + 1 < len(args):
            out = args[i + 1]

    label = week_label()
    reviews_dir = data / "memory" / "reviews"
    draft = ""
    if reviews_dir.is_dir():
        drafts = sorted(reviews_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if drafts:
            draft = drafts[0].read_text(encoding="utf-8")[:2000]

    st = StatsService(data).compute()
    q = st.pop("队列", {})

    report_dir = data / "memory" / "reports"
    report_dir.mkdir(exist_ok=True)
    out_path = Path(out) if out else report_dir / f"weekly-{label}.md"

    lines = [
        f"# 周报 · {label}", "",
        f"> 生成: {datetime.date.today().isoformat()} | 数据目录: {data}", "",
        "## 本周回顾草稿（节选）", "",
        draft.strip() or "（本周无回顾草稿，运行 anote review）", "",
        "## 数据统计", "",
        f"- 📝 笔记 **{st.get('笔记总数', 0)}** · 📄 论文 **{st.get('论文精读', 0)}** · 📚 书 **{st.get('教科书', 0)}**（章 {st.get('章节', 0)}）",
        f"- 📥 队列 " + " ".join(f"{k}{q.get(k, 0)}" for k in ("📥", "📖", "✅", "🗄")),
        f"- 🔄 回顾草稿 **{st.get('回顾草稿', 0)}** · 📚 引用 **{st.get('引用条目', 0)}**", "",
        "## 下周建议", "- 精读队列中待读（📥）论文",
        "- 运行 anote wiki 更新主题页（如笔记有新增）", "- 季度审视 roadmap.md", "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
