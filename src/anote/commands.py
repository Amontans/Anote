"""Anote 命令注册表（v1.16 单一来源）。

- TUI 命令面板/帮助页直接消费本表；
- tests/test_commands.py 校验 `anote` 入口的 case 与注册表一致。
新命令必须：① 在此注册 ② 在 anote 中加 case ③ 在 INTERFACES 中登记。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandMeta:
    name: str          # 注册表主名
    case: str          # anote 入口 case 模式（可含 | 别名）
    syntax: str        # 用户可见语法
    help: str          # 一句话说明
    example: str = ""


COMMAND_META = [
    CommandMeta("tui", "tui", "anote tui", "打开 TUI 界面"),
    CommandMeta("edit", "edit", "anote edit <路径>", "用配置的编辑器打开笔记"),
    CommandMeta("new", "new", 'anote new <学科/分支> <标题> [--template note|note-math]', "新建笔记（不覆盖同名）",
                '例: anote new 数学/代数 "群论基础"'),
    CommandMeta("daily", "daily", "anote daily", "今日笔记（含队列快照）"),
    CommandMeta("search", "search", 'anote search "<关键词>"', "文献检索并入队（arXiv/S2/OpenAlex/Crossref）"),
    CommandMeta("ask", "ask", 'anote ask "<问题>" [--semantic]', "知识库问答（grep/混合检索）",
                '例: anote ask --semantic "环是什么"'),
    CommandMeta("ask-pi", "ask-pi", 'anote ask-pi "<问题>"', "经 Pi 回答（可检索知识库）"),
    CommandMeta("ai", "ai", 'anote ai "<自然语言>"', "说人话，AI 转成白名单命令执行",
                '例: anote ai "帮我找关于X的论文"'),
    CommandMeta("init-data", "init-data", "anote init-data", "幂等初始化数据根骨架"),
    CommandMeta("index", "index", "anote index", "重建分层 00-index 索引"),
    CommandMeta("index-semantic", "index-semantic", "anote index-semantic [--full]", "重建/增量语义索引"),
    CommandMeta("check", "check", "anote check [--strict]", "一致性自检（8 项）"),
    CommandMeta("stats", "stats", "anote stats [--json]", "统计各类文件数"),
    CommandMeta("migrate", "migrate", "anote migrate --to <路径>", "迁移数据根（含 .git 与 .anote 配置）"),
    CommandMeta("review", "review", "anote review [--days N]", "生成周/月回顾草稿"),
    CommandMeta("project", "project", "anote project <名> [目标]", "新建研究项目"),
    CommandMeta("book", "book", 'anote book <书名> [作者]', "新建教科书（ctexbook）"),
    CommandMeta("chapter", "chapter", "anote chapter <书名> <章名>", "添加章节"),
    CommandMeta("book-build", "book-build", "anote book-build <书名>", "编译教科书 PDF"),
    CommandMeta("read", "read", "anote read <路径>", "统一阅读（读即登记）",
                "例: anote read pdfs/2402.00001.pdf"),
    CommandMeta("paper-read", "paper-read|读论文", "anote paper-read <arxiv-id>", "下载+提取+精读笔记+登记一条龙"),
    CommandMeta("docs", "docs", "anote docs {list|add|update|progress|stats|import|annotations}", "文档管理（registry 登记表）"),
    CommandMeta("paper", "paper", 'anote paper <主题> [--type 论文|综述|开题]', "论文骨架 + 素材聚合",
                '例: anote paper "环论" --type 综述'),
    CommandMeta("wiki", "wiki", "anote wiki [--dry] [--force]", "知识编译：笔记 → 学科主题页"),
    CommandMeta("meta", "meta", "anote meta [--ai]", "META 检查/经 Pi 补全建议"),
    CommandMeta("graph", "graph", "anote graph [--mermaid]", "知识图谱（标签/反链）"),
    CommandMeta("report", "report", "anote report", "周报自动生成"),
    CommandMeta("backlinks", "backlinks", 'anote backlinks "<概念>"', "反链视图"),
    CommandMeta("zotero", "zotero", "anote zotero {status|bib|setup}", "Zotero 文献接入"),
    CommandMeta("bibcheck", "bibcheck", "anote bibcheck", "引用链路校验"),
    CommandMeta("convert", "convert", "anote convert <文件> [--out 输出]", "文档转换（pandoc 40+ 格式）"),
    CommandMeta("ebook", "ebook", "anote ebook [list|extract]", "电子书管理/提取文本"),
    CommandMeta("index-pdf", "index-pdf", "anote index-pdf", "批量提取 PDF 文本"),
    CommandMeta("backup-create", "backup-create", "anote backup-create [--encrypt]", "备份到 .anote/backups"),
    CommandMeta("restore", "restore", "anote restore <文件> [--dry-run]", "备份恢复/演练"),
    CommandMeta("archive", "archive", "anote archive <年份> [--dry]", "年度归档（自动排除检索）"),
    CommandMeta("web", "web", "anote web [--port N]", "只读浏览外壳（仅本机）"),
    CommandMeta("export", "export", "anote export [--out 路径]", "整库打包导出"),
    CommandMeta("mcp", "mcp", "anote mcp", "MCP Server（供外部 AI 工具调用）"),
    CommandMeta("external", "external", "anote external {list|call}", "消费外部 MCP server"),
    CommandMeta("plugin", "plugin", "anote plugin {list|add|run}", "插件机制"),
    CommandMeta("lint", "lint", "anote lint <tex文件>", "LaTeX 语法检查（chktex）"),
    CommandMeta("md", "md", "anote md <文件> [--watch]", "终端 Markdown 渲染"),
    CommandMeta("preview", "preview", "anote preview <文件> [--watch]", "MD/TEX 浏览器预览"),
    CommandMeta("checklist", "checklist", "anote checklist", "投稿前检查清单"),
    CommandMeta("eval", "eval", "anote eval [--k N]", "检索质量评测"),
    CommandMeta("commit", "commit", 'anote commit [说明]', "提交（自动索引+自检）"),
    CommandMeta("backup", "backup", "anote backup", "git 提交并推送远程"),
    CommandMeta("config", "config", "anote config [set <键> <值>]", "查看/修改配置（数据根内 .anote/config）"),
    CommandMeta("test", "test", "anote test", "一键测试门禁"),
    CommandMeta("release", "release", "anote release <major|minor|patch>", "发布门禁（测试+版本+tag）"),
    CommandMeta("help", "help|-h|--help", "anote help [<命令>]", "帮助"),
]


def command_by_name(name: str) -> CommandMeta | None:
    for meta in COMMAND_META:
        if meta.name == name:
            return meta
    return None
