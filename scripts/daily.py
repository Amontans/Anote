#!/usr/bin/env python3
"""每日笔记：创建/返回今天的笔记（src/日志/YYYY-MM-DD.tex），附当日队列快照。

用法:
  daily.py             # 创建（若不存在）并打印路径
  daily.py --open      # 打印路径（由 anote daily 打开编辑器）
"""
import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anote_config import data_dir as cfg_data_dir  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", action="store_true")
    a = ap.parse_args()
    data = cfg_data_dir()
    today = datetime.date.today().isoformat()
    d = os.path.join(data, "src", "日志")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{today}.tex")
    if not os.path.exists(path):
        # 当日队列快照
        q = "📥0 📖0 ✅0 🗄0"
        try:
            text = open(os.path.join(data, "queue.md"), encoding="utf-8").read()
            q = " ".join(f"{k}{text.count(k)}" for k in ("📥", "📖", "✅", "🗄"))
        except Exception:  # noqa: BLE001
            pass
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
  \\item 队列快照：{q}
  \\item 回顾：memory/reviews/（anote review 生成）
\\end{{compactitem}}

\\section{{今日记录}}
\\begin{{compactitem}}
  \\item 
\\end{{compactitem}}

\\end{{document}}
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    print(path)


if __name__ == "__main__":
    main()
