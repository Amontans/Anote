#!/usr/bin/env python3
"""Generate a paper skeleton (LaTeX or Markdown), bilingual annotations."""
import argparse
import datetime
import os

LATEX_TMPL = r"""% ===== 论文骨架（自动生成）=====
% 编译: xelatex + bibtex（中文需 xelatex + ctex 宏包）
\documentclass[11pt]{article}
% 中文支持: \usepackage{ctex}  （已装 texlive-lang-chinese 时可用）
\usepackage[margin=1in]{geometry}
\usepackage{graphicx,booktabs,amsmath,amssymb}
\usepackage[colorlinks=true]{hyperref}

\title{%%TITLE%%}
\author{%%AUTHOR%%}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
% 五句法则: 背景→问题→方法→结果→影响
% 1. 研究背景与重要性（1句）
% 2. 现有方法局限 / 未解决问题（1句）
% 3. 本文方法概述（1-2句）
% 4. 关键结果/性能数字（1-2句）
% 5. 研究意义 / 影响（1句）
\end{abstract}

\section{Introduction}
% 漏斗结构: 大背景 → 具体任务 → 已有工作 → gap → 本文贡献列表（3条左右）
% 末段通常给出本文 contributions 与论文组织（outline）

\section{Related Work}
% 按主题分小节; 每组用"这些工作的共同局限是..."收尾, 自然引出本文

\section{Method}
% 先给总体架构（图1）+ 数学记号表; 每个组件单独小节;
% 每个设计决策回答: 为什么这样做? 不这样做会怎样?

\section{Experiments}
% 设置（数据集/基线/指标/实现细节）→ 主结果（表）→ 消融 → 分析
% 每个表都要在正文引用: "Table \ref{tab:main} shows..."

\section{Conclusion}
% 总结贡献 + 主动写 2-3 条局限 + 未来工作

\bibliographystyle{unsrt}
\bibliography{refs}

\end{document}
"""

MD_TMPL = """# %%TITLE%%

> 生成日期: %%DATE%% | 草稿 → 定稿流程：大纲 → 初稿 → 自检 → AI 润色 → 终稿

## Abstract（五句法则）
1. 背景：
2. 问题：
3. 方法：
4. 结果：
5. 影响：

## 1. Introduction
- [ ] 研究背景（漏斗式：大 → 小）
- [ ] 现有工作与空白（gap）
- [ ] 本文贡献（3 条，列表）
- [ ] 论文组织（outline）

## 2. Related Work
- [ ] 主题分组
- [ ] 每组"共同局限"收尾

## 3. Method
- [ ] 总体架构（图）
- [ ] 记号表 / 问题定义
- [ ] 各组件小节

## 4. Experiments
- [ ] 设置（数据集/基线/指标）
- [ ] 主结果表
- [ ] 消融与分析

## 5. Conclusion
- [ ] 总结
- [ ] 局限（2-3 条）
- [ ] 未来工作

## References
> 用 literature-search 导出 BibTeX；pandoc --citeproc 渲染
"""


def main():
    ap = argparse.ArgumentParser(description="New paper skeleton")
    ap.add_argument("name", help="论文名（会用于文件名与标题）")
    ap.add_argument("--lang", default="en", choices=["en", "zh"])
    ap.add_argument("--fmt", default="latex", choices=["latex", "md"])
    ap.add_argument("--author", default="")
    ap.add_argument("--dir", default=".")
    a = ap.parse_args()

    out_dir = os.path.expanduser(a.dir)
    os.makedirs(out_dir, exist_ok=True)
    title = a.name.replace("_", " ").title() if a.lang == "en" else a.name
    ext = "tex" if a.fmt == "latex" else "md"
    out = os.path.join(out_dir, f"{a.name}.{ext}")
    if a.fmt == "latex":
        content = (LATEX_TMPL.replace("%%TITLE%%", title)
                             .replace("%%AUTHOR%%", a.author or "Your Name"))
    else:
        content = MD_TMPL.replace("%%TITLE%%", title) \
                         .replace("%%DATE%%", datetime.date.today().isoformat())
    with open(out, "w") as f:
        f.write(content)
    print(f"骨架已生成: {out}")


if __name__ == "__main__":
    main()
