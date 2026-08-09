# 变更日志（CHANGELOG）

## [Unreleased] - 0.8.0-dev（TUI 开发中）

### 新增
- **TUI 框架（P0+P1）**：Textual 8.2.8；`notes tui` 启动
  - `AnoteContext` 数据总线：配置/数据/脚本三接口统一（后续部件唯一依赖点）
  - `commands.py` 命令元数据单一表（帮助页+命令面板共用）
  - 屏幕注册表：Home/Settings/Help + 5 个契约化占位页（Notes/Queue/Memory/Books/Review）
  - 全局键位（ctrl 组合，输入框聚焦不冲突）：Ctrl+H/N/Q/M/B/R 导航、Ctrl+S 设置、F1 帮助、F5 自检、Ctrl+P 命令面板、Ctrl+D 退出
  - 设置页：数据目录/编辑器（可选 code/vim/nvim/emacs/gedit/nano）/语言；保存即写配置
  - 无头冒烟测试 `tui/test_smoke.py`（Textual Pilot，8 项断言）
- **配置层**：`scripts/anote_config.py`（~/.config/anote/config，bash/python 双解析）；全部脚本默认路径改读配置
- **编辑器可选择性**：`editor` 配置项（设置页 Select）

### 变更
- 全局导航键从单字母改为 Ctrl 组合（Textual 8.x：输入框聚焦时吞掉纯字母键，Ctrl 组合可靠）
- 语义索引：`notes index-semantic` 移入 manage.sh（P0 配置化）

### 待办（P2/P3）
- 数据页实装（Notes/Queue/Memory/Books/Review）
- 数据迁移向导（含 .git 一起搬 + 校验回滚）


本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 风格。版本号遵循语义化版本（SemVer）。

## [0.6.0] - 2026-08-09

### 新增
- **一键自举**：`setup.sh`（依赖检查/venv/索引/自检，幂等，可重建整个系统）
- **AI 操作协议**：README 内置——任何 AI 助手读文档即可独立答疑与辅助学习（红线/流程明确）

### 变更
- 文档精简合并：WORKFLOW 并入 README；EXTENDING+UPGRADING → `docs/DEVELOPMENT.md`（架构/接口文档保留）
- 删除 `notes.py`（旧 Markdown 流程，已被 `--tex-note` TEX 流程取代）；INTERFACES/技能文档同步清理

## [0.5.0] - 2026-08-09

### 新增
- **语义向量检索（B 方案）**：`scripts/embed.py`（fastembed bge-small-zh + numpy 缓存，增量更新）+ `notes ask --semantic`
- **教科书输出层**：`books/` ctexbook 模板 + `notes book / chapter / book-build` 命令（实测编译出完整 PDF）
- **文档体系**：README + `docs/{ARCHITECTURE,INTERFACES,WORKFLOW,EXTENDING,UPGRADING}.md` + CHANGELOG + LICENSE
- **接口契约**：`docs/INTERFACES.md` 定义全部数据格式/CLI/缓存/钩子契约；缓存加入 `schema_version`
- 脚手架：`notes new`（META 笔记模板）、`notes project`

### 变更
- 脚本从 Pi skills 迁入项目 `scripts/`（单一真相源，随项目版本化）；skills 文档与规则路径已同步
- `.semantic/` 缓存格式 v1：`{schema_version, chunks[]}`

### 修复
- embed.py 增量逻辑：空内容文件不再反复重嵌
- check.py：嵌套索引匹配、转义文件名匹配、PDF 后缀匹配

## [0.4.0] - 2026-08-07

### 新增
- `notes ask` 关键词片段检索（省 token）
- XDG 规范化：项目迁至 `~/Documents/Anote`
- pre-commit 钩子（自动索引 + 自检提示）、systemd 周回顾定时器、`manage.sh` 一键命令

## [0.3.0] - 2026-08-07

### 新增
- 论文待读队列（queue.tex，📥→📖→✅→🗄 状态机）
- 项目层（projects/plan.tex + log.tex）、路线图（roadmap.tex）
- 自检雷达 `check.py`（6 项）、`index-gen.py` 分层索引、备份脚本

## [0.2.0] - 2026-08-07

### 新增
- 记忆生长闭环：research-log / insights / concepts / open-questions + `review.py` 回顾草稿
- Pi 行为规则（academic-memory.md）

## [0.1.0] - 2026-08-07

### 新增
- 初始结构：src/ 学科笔记 + latexmkrc + git 版本控制
