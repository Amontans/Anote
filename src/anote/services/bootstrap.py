"""数据目录自举服务：创建新数据目录骨架（幂等，绝不覆盖已有用户文件）。"""
from __future__ import annotations

import shutil
from pathlib import Path

from ..core import PROJECT_ROOT, Config, config_path_for

MEMORY_FILES = {
    "research-log.md": "# 研究日志\n\n> 每次学术会话后追加：做了什么、读了什么、关键结论、下一步。\n",
    "insights.md": "# 洞见库\n\n> 每一条：一句话洞见 + 来源（论文/笔记/讨论）。宁缺毋滥。\n",
    "concepts.md": "# 概念库\n\n> 每一条：**概念**：定义——来源。\n",
    "open-questions.md": "# 开放问题\n\n> 每一条：问题（背景/相关笔记/状态：开放|解决中|已解决+日期）。\n",
}

QUEUE_TMPL = """# 论文待读队列

> 状态: 📥待读 → 📖在读 → ✅已精读 → 🗄已归档。由 AI 维护。

| 状态 | 日期 | 论文 | arXiv/DOI | 笔记 |
|------|------|------|-----------|------|
"""

ROADMAP_TMPL = """# 研究路线图

## 季度目标
-

## 进行中
-

## 待读文献
-

## 每月审视
- 记录：本月进展 / 偏离 / 下月调整
"""

README_TMPL = """# Anote 数据目录（个人知识库）

> 本目录是 Anote 的**唯一用户数据根**：知识、配置、日志、备份都在这里。
> 项目代码与数据分离；迁移时整目录拷贝即可。

| 路径 | 是什么 |
|------|--------|
| `src/` | 学习笔记（唯一真相源，TEX） |
| `memory/` | 记忆层（日志/洞见/概念/问题/回顾） |
| `books/` `projects/` | 教科书 / 研究项目 |
| `pdfs/` `ebooks/` `docs/registry.md` | 文献与文档库 |
| `queue.md` `roadmap.md` `refs.bib` | 队列 / 路线图 / 引用库 |
| `.anote/` | 配置、日志、外部 MCP 注册、备份（`.anote/backups/`） |
| `.semantic/` `.venv/` | 可重建缓存 |

## 维护
- 改完笔记：`anote commit "说明"`（自动索引+自检）
- 备份：`anote backup-create`（默认写入 `.anote/backups/`，可 `--out` 外置冷备）
- 换电脑：拷贝本目录 + 项目目录 → `./setup.sh` → `anote check`
"""


def _copy_template(rel: str, dst: Path) -> None:
    if dst.exists():
        return
    src = PROJECT_ROOT / "templates" / rel
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)


def ensure_data_dir(data_dir: Path | None = None) -> dict[str, int]:
    """创建新数据目录骨架。返回 {created_dirs, created_files}。"""
    data = Path(data_dir) if data_dir else Config.load().data_dir
    created_dirs, created_files = 0, 0

    def mkdir(p: Path) -> None:
        nonlocal created_dirs
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created_dirs += 1

    def write(p: Path, content: str) -> None:
        nonlocal created_files
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            created_files += 1

    for d in ("src", "memory/reviews", "memory/reports", "books", "projects",
              "pdfs", "ebooks", "docs", ".anote"):
        mkdir(data / d)

    for name, content in MEMORY_FILES.items():
        write(data / "memory" / name, content)
    write(data / "queue.md", QUEUE_TMPL)
    write(data / "roadmap.md", ROADMAP_TMPL)
    write(data / "README.md", README_TMPL)
    write(data / "refs.bib", "% 引用库（Zotero/Better BibTeX 导出或 anote search --bib）\n")

    # 配置：只在不存在时生成默认值
    cfg_path = config_path_for(data)
    if not cfg_path.exists():
        cfg = Config.load()
        cfg.data_dir = data
        cfg.save()
        created_files += 1

    # 数据目录 gitignore（首次写入；已有文件不覆盖）
    if not (data / ".gitignore").exists():
        (data / ".gitignore").write_text(
            "# 可重建/运行产物不入 git\n"
            ".venv/\n.semantic/\n.anote/\n"
            "__pycache__/\n*.pyc\n"
            "# PDF 附件与编译产物\n"
            "pdfs/\n*.aux\n*.log\n*.out\n*.fls\n*.fdb_latexmk\n*.synctex.gz\n"
            "*.bbl\n*.blg\n*.toc\n*.nav\n*.snm\n*.vrb\n*.pdf\n",
            encoding="utf-8")
        created_files += 1

    # 教科书/项目模板
    _copy_template("book/main.tex", data / "books/_template/main.tex")
    _copy_template("book/chapters/ch01.tex", data / "books/_template/chapters/ch01.tex")
    _copy_template("book/latexmkrc", data / "books/_template/latexmkrc")
    _copy_template("book/refs.bib", data / "books/_template/refs.bib")
    mkdir(data / "books/_template/figures")
    _copy_template("project/plan.tex", data / "projects/_template/plan.tex")
    _copy_template("project/log.tex", data / "projects/_template/log.tex")

    return {"created_dirs": created_dirs, "created_files": created_files}
