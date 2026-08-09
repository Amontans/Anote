#!/usr/bin/env python3
"""每日笔记（薄适配器）：逻辑在 src/anote/services.py + core。"""
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import QueueService  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote import cli as _cli  # noqa: E402

def main() -> None:
    data = Config.load().data_dir
    today = datetime.date.today().isoformat()
    d = Path(data) / "src" / "日志"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{today}.tex"
    if not path.exists():
        q = QueueService(data).counts()
        snap = " ".join(f"{k}{q.get(k, 0)}" for k in ("📥", "📖", "✅", "🗄"))
        content = f"""% ==META== 学科: 日志 | 分支: 每日 | 标签: 日记 | 日期: {today} | 来源: 其他
\\documentclass[11pt]{{ctexart}}
\\usepackage[margin=2.5cm]{{geometry}}
\\usepackage{{paralist}}
\\title{{{today} 日志}}
\\date{{{today}}}

\\begin{{document}}
\\maketitle

\\section{{今日概览}}
\\begin{{compactitem}}
  \\item 队列快照：{snap}
  \\item 回顾：memory/reviews/（anote review 生成）
\\end{{compactitem}}

\\section{{今日记录}}
\\begin{{compactitem}}
  \\item 
\\end{{compactitem}}

\\end{{document}}
"""
        path.write_text(content, encoding="utf-8")
    print(path)


if __name__ == "__main__":
    sys.exit(_cli.run(main))
