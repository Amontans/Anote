#!/usr/bin/env python3
"""anote checklist —— 投稿前检查清单（v1.10）。

接口声明（契约）:
    输入: argv（无）
    输出: stdout=检查清单；退出码 0
    副作用: 无
"""
import sys

CHECKLIST = """📋 投稿前检查清单（anote 学术写作）

## 内容
- [ ] Abstract 五句法则：背景→问题→方法→结果→影响
- [ ] 每个图表在正文中被引用并解释（"Figure N shows..."）
- [ ] 术语全文一致（同一概念统一用词）
- [ ] 时态：相关工作过去时；本文方法/图表一般现在时
- [ ] Limitation 主动写 2-3 条

## 引用
- [ ] anote bibcheck 通过（无缺失引用键）
- [ ] 无"孤儿引用"（参考文献每个都被正文引用）
- [ ] 引用格式符合目标会议/期刊样式（unsrt/IEEEtran 等）

## 工程
- [ ] 编译无警告: latexmk -lualatex paper.tex（2 遍 + bibtex）
- [ ] 图表文件路径正确（figures/ 目录）
- [ ] PDF 导出检查（目录/公式/引用渲染正常）
- [ ] 版本提交: git add -A && git commit（可回滚）

## 复现性（科研加分项）
- [ ] 实验设置/超参数/数据划分写清
- [ ] 代码/数据链接或附录说明
"""


def main() -> int:
    print(CHECKLIST)
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
