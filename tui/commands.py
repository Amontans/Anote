#!/usr/bin/env python3
"""命令元数据（单一表）：帮助页 + 命令面板共用，避免双份维护。"""
from textual.command import Hit, Provider

COMMANDS = [
    ("index", "notes index", "重建分层索引"),
    ("index-semantic", "notes index-semantic", "重建/增量语义索引"),
    ("check", "notes check", "运行 6 项一致性自检"),
    ("review", "notes review --days 7", "生成周回顾草稿"),
    ("ask", 'notes ask --semantic "问题"', "语义问答（省 token）"),
    ("new", 'notes new 学科/分支 "标题"', "新建笔记（自动 META 模板）"),
    ("book", 'notes book "书名"', "新建教科书（ctexbook）"),
    ("book-build", 'notes book-build "书名"', "编译教科书 PDF"),
    ("chapter", 'notes chapter "书名" "章名"', "添加章节"),
    ("project", 'notes project "名" "目标"', "新建研究项目"),
    ("commit", 'notes commit "说明"', "提交（自动索引+自检）"),
    ("backup", "notes backup", "提交并推送远程"),
    ("tui", "notes tui", "打开本 TUI"),
]

BINDINGS_HELP = [
    ("F1", "帮助"),
    ("Ctrl+F", "全文搜索"),
    ("Ctrl+A", "AI 问答（经 Pi）"),
    ("Ctrl+H / N / Q / M / B / R", "主页 / 笔记 / 队列 / 记忆 / 书 / 回顾"),
    ("Ctrl+S", "设置"),
    ("F5", "运行自检"),
    ("Ctrl+D", "退出"),
    ("（输入框内直接打字，不影响导航）", ""),
]


class AnoteCommands(Provider):
    """命令面板：模糊搜索全部 Anote 命令。"""

    async def discover(self):
        for key, cmd, desc in COMMANDS:
            yield Hit(display=key, command=cmd, help=desc)

    async def search(self, query):
        q = query.lower()
        for key, cmd, desc in COMMANDS:
            if q in key.lower() or q in desc.lower():
                yield Hit(display=key, command=cmd, help=desc)
