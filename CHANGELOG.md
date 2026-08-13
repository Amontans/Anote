# 变更日志（CHANGELOG）

## [1.14.1] - 2026-08-13（提示与辅助增强）

### 变更
- 移除中文别名（保持命令精简，用户反馈）
- **未知命令模糊建议**：`anote chekc` → "你是不是想说: anote check ?"（difflib）
- **下一步提示**：new 后提示 commit；commit 后提示 backup
- **`anote help <命令>` 带示例**：usage 行 + 常见用法实例（example_of 表）

## [1.14.0] - 2026-08-13（使用体验优化：说人话即可）

### 新增（减少记忆负担）
- **中文/短别名**：问/读/记/写/书/文献/查/统计/存/备份/回顾/转换/读论文/帮助 → 对应英文命令
- **`anote` 无参数 → 友好菜单**（常用 10 条，不再打印长 usage）
- **`anote ai "<自然语言>"`**：经 Pi 把"人话"转成命令并执行（实测："查看我的知识库统计"→anote stats）
- **`anote 读论文 <arxiv-id>`**：下载+提取+精读笔记+登记 一条龙

## [1.13.0] - 2026-08-13（剩余项补齐：lint/标注绑定/评测闭环/分层检索）

### 新增
- **`anote lint <tex>`**：LaTeX 语法/风格检查（chktex 包装；texlab 可装补全）
- **标注自动绑定**：`anote docs annotations` 自动按文件名匹配 src/papers/ 精读笔记（无匹配则归档）
- **检索评测闭环**：ask 无命中查询 → memory/query-failures.log；`anote eval` 读取并建议补评测集
- **分层检索**：`anote ask --semantic --layer notes|docs`（笔记层 vs 文档层）

### 修复
- ask 参数解析：带值 flag（--layer 等）的值不再被误当 query；分层用相对路径判断

## [1.12.0] - 2026-08-13（基础→上层依次实现）

### 基础层
- **setup.sh 分层安装**：`--minimal`（核心零第三方依赖）/ `--full`（默认，含 fastembed/textual/fastmcp）

### 协议层
- **MCP client**：`anote external {list|call <名> <工具>}`；services/mcp_client.py（JSON-RPC over stdio）；配置 ~/.config/anote/external.json；自举验证（调用自身 MCP server 成功）

### 应用层
- **M4 Zotero 标注导入**：`anote docs annotations <标注文件> [--to 笔记]`
- **M5 文档语义索引层**：语义索引纳入 pdfs/ebooks 的 txt 文本（anote ask --semantic 覆盖文档层）

## [1.11.0] - 2026-08-13（大模型升级后审计：轻量+任意IO）

### 审计结论（docs/AUDIT.md）
- **轻量**：核心零第三方依赖；语义检索/TUI/MCP 全部懒加载；BM25 兜底可脱离 fastembed
- **任意 I/O**：pandoc(40+格式) + portkit(任意插件↔任意) + MCP(任意 AI 工具) 三枢纽

### 新增
- **`anote convert`**（pandoc 包装）：40+ 格式双向转换（实测 md→docx/html/pdf 链）；中文 PDF 用 xelatex+CJK
- docs/AUDIT.md 轻量+IO 审计报告

### 待办
- setup.sh 分层安装（--minimal/--full）；MCP client；LSP 接入

## [1.10.0] - 2026-08-10（专业级阅读与管理 M1-M3）

### 新增
- **`anote docs` 文档管理**（专业图书级）：docs/registry.md 契约登记表（状态/类型/文件/标题/作者/年份/标签/笔记/进度/最后阅读/哈希）
  - `docs list`（--status/--tag/--type/--sort 过滤排序）、`docs add`（sha256 去重）、`docs update`、`docs progress`、`docs stats`（未读占比）、`docs import`（批量扫描 pdfs/ebooks + 提取文本）
- **`anote read` 读即登记**：打开自动登记/📥→📖/记录最后阅读/提示上次进度；路由：pdf→zathura、epub→foliate、mobi→calibre（foliate/calibre 已安装）
- **check 第 8 项**：文档登记一致性；**stats 并入**文档/在读统计
- services/docs.py（DocService 全逻辑）；单测 17 项全绿（新增 TestDocs）

## [1.9.1] - 2026-08-10（文档阅读补全）

### 新增（填补 PDF/MOBI 处理缺口）
- **`anote read <路径>`**：统一阅读入口（PDF→zathura/okular；epub→foliate 若有；自动选阅读器，config 可设 reader）
- **`anote ebook [list|extract]`**：电子书目录 + epub 文本提取（stdlib zipfile+HTML 解析，零依赖）；mobi 提示装 calibre
- **`anote index-pdf`**：批量提取 pdfs/*.pdf → .txt（**PDF 内容可被 `anote ask` 检索**）
- services/ebooks.py（extract_epub/extract_pdf_text/pick_reader）
- 单测 16 项全绿（新增 TestEbook）

### 修复
- ripgrep 绝对根目录下 `pdfs/*.txt` glob 失效 + .gitignore 跳过 pdfs → ask 改为 cwd=数据目录+--no-ignore（PDF 文本可检索）

## [1.9.0] - 2026-08-10（v1.10 写作输出）

### 新增
- **`anote paper <主题> [--type 论文|综述|开题] [--no-ai] [--dry]`**：素材聚合（BM25/向量检索+refs.bib 引用+wiki 主题页）→ 经 Pi 生成 LaTeX 骨架 → projects/<主题>/{paper.tex, materials.md}；无 fastembed 时 BM25 兜底
- **`anote checklist`**：投稿前检查清单（内容/引用/工程/复现性）
- 单测 15 项全绿（新增 TestPaper）

## [1.8.0] - 2026-08-10（v1.9 检索质量）

### 新增
- **混合检索**：services/retrieval.py（BM25 词法（中文 2-gram，零依赖）+ 向量余弦加权融合 + 轻量重排）；`anote ask --semantic` 升级为混合，`--bm25` 纯词法
- **`anote eval [--k N]` 检索评测**：自命中率 + 人工查询集（memory/eval-queries.md，实测 4/4=100%）
- 单测 14 项全绿（新增 TestRetrieval：BM25 排序/分词）

## [1.7.0] - 2026-08-10（模块化收官 + P0 备份恢复）

### 重构（简洁化到优秀）
- **services 包 15 领域**：新增 literature/migration/index/zotero/papers；search/migrate/index-gen/zotero/fetch_paper 五脚本变薄适配器
- 全部脚本 ≤150 行、无业务逻辑；领域逻辑统一在 services

### 新增（v1.8 P0 备份恢复）
- **`anote backup-create [--encrypt]`**：tar.gz + SHA256 校验（openssl AES-256 可选加密，ANOTE_BACKUP_KEY）
- **`anote restore <文件> [--dry-run/--force]`**：校验和验证 + 演练预览 + 还原（剥离顶层目录）
- **`anote archive <年份>`**：旧笔记归档到 src/_archive/（自动排除在检索外）
- 每日备份定时器：周日自动加密冷备（设 ANOTE_BACKUP_KEY 后启用）

## [1.6.1] - 2026-08-10（模块化/简洁化到优秀）

### 重构
- **services 包补全**：health（7 项自检）/ wiki / graph / meta / review / semantic 六领域迁入 services/，对应脚本变薄适配器
- **语义检索共享**：chunk_text/建索引/检索 → SemanticService（embed.py 与 ask.py 共用，消除重复）
- **TUI 去重**：context.queue_counts/note_count 改用 QueueService/NotesService（不再内联解析）
- **修复**：ask --smart 停用词原为字符集（误删"论"等字）→ 显式词表；ask 参数顺序兼容（--semantic 可前置）；health [2] 队列正则适配 MD 格式
- **简洁化清单**：CODING.md 新增 5 条代码评审检查项

## [1.6.0] - 2026-08-10（体验与图谱 + 模块化）

### 新增
- **`anote graph [--mermaid]`**：知识图谱（META 标签 → 引用笔记，邻接表 + mermaid 流程图）
- **`anote report`**：周报自动生成（回顾草稿节选 + 数据统计 + 下周建议，memory/reports/）
- **TUI 主题系统**：Settings 选择（textual-dark/light/nord/gruvbox/monokai/tokyo-night），保存即生效
- **帮助分层**：`anote help <命令>` 单命令详解
- **流程完善**：docs/PROCESS.md（六步版本生命周期）+ `anote release <major|minor|patch>` 发布门禁
- **模块化重构**：services.py → services/ 包（queue/notes/stats/bib 一领域一模块，向后兼容重导出）

## [1.5.0] - 2026-08-10（多端协作 + CI 门禁）

### 新增
- **`anote test` 一键测试门禁**（单测+TUI 冒烟+TUI 动作+check；pre-push 钩子阻塞失败推送）
- **每日自动备份定时器**（notes-backup.timer 23:00，commit+push）
- **`anote web`**：只读浏览外壳（仅 127.0.0.1，可选 --token，全文搜索）
- **`anote export`**：整库打包（排除 .venv/.semantic/.git，可移植）
- **流程科学性**：ROADMAP 新增 DoD/依赖图/风险登记/优先级/验证节奏

## [1.4.0] - 2026-08-10（知识编译 + 数据质量）

### 新增
- **`anote wiki` 知识编译层**（LLM Wiki 范式）：按 学科/分支 把 src/ 笔记经 Pi 编译成 L1 主题页（wiki/目录，MD 派生产物可重建）；--dry/--force/--branch
- **`anote meta`**：META 完整性报告；--ai 经 Pi 生成补全建议（实测：标签建议+学科对齐提示）
- **AI provider 抽象**：`core.ai_ask()` 统一 AI 入口（Config.ai_provider，默认 pi 代理；未来可扩展直连，对上层透明）
- 单测 12 项全绿（新增 TestWikiGroup）

## [1.3.0-dev] - 2026-08-10（Zotero 文献闭环）

### 新增
- Better BibTeX 9.0.55 插件已下载（~/Downloads/zotero-better-bibtex-9.0.55.xpi，待 GUI 安装）
- `anote zotero {status|bib|setup}`：状态/refs.bib 统计/接入指引
- `anote bibcheck`：引用链路校验（笔记 cite ↔ refs.bib 一致性，缺失键/冗余条目）
- ROADMAP 自审：规划欠缺分析（备份恢复/检索质量/写作输出/AI 降级/META 自动补全/CI/访问控制/归档/帮助分层）
- **BibService 进 services**（bibcheck/check/stats/MCP 共用，DRY；跳过 LaTeX 注释）
- `anote check` 新增第 7 项：引用链路校验
- `anote stats` 新增「引用条目」；MCP 新增 `anote_bib` 工具（6 工具）
- 单测 11 项全绿（含 TestBibService）
- 全链路沙盒验证：bibcheck ✓ → latexmk 编译 → PDF 渲染引用 ✓；BIBINPUTS 方案固化进根 latexmkrc
- `anote zotero status` 直读 Zotero 库条目数（~Zotero/zotero.sqlite 只读）+ BBT 检测

## [1.2.0] - 2026-08-09（插件 + MCP + 现代化完善）

### 新增
- **插件机制**：`plugins/` 目录 + `anote plugin {list|add|run}`（示例插件已装）
- **MCP Server**：`anote mcp`（stdio，fastmcp）；5 工具（anote_stats/search/ask/queue/notes）；实测握手+调用全通
- **统一 CLI 基础设施**：`src/anote/cli.py`（run 守卫：异常→单行可读错误+退出码；Result 自动输出）
- **模块契约声明**：全部 15 个脚本 docstring 含"接口声明（输入/输出/副作用）"
- **配置单点化**：anote_config.py 重构为 core.Config 兼容层（消除双解析）
- **MCP 测试**：tests/test_mcp.py（握手 + 工具调用）
- **发展方向规划**：ROADMAP 新增愿景（知识编译层/插件生态/Pi 互操作/开源发布）

### 修复
- fastmcp 横幅污染 stdout → 显式 transport="stdio"

## [1.1.0] - 2026-08-09（AI 深度集成 · 经 Pi + 现代化改造）

### 新增（v1.1 路线图三项）
- **反链视图**：`anote backlinks "<概念>"`（rg 计数 + META 标签命中）
- **回顾自动化**：定时器改为 `weekly-review.sh`（生成草稿 + 自动 git 提交）
- **语义索引自动增量**：pre-commit 钩子自动重嵌入变更文件

### 代码现代化改造（docs/CODING.md）
- **src-layout 包**：`src/anote/`（core.py：Config dataclass/Result/setup_logging；services.py：QueueService/NotesService/StatsService）
- **薄适配器**：stats.py / daily.py 重构为调包（消除 bootstrap 重复）
- **单元测试**：`tests/test_core.py`（8 项，临时目录隔离）

### 新增
- **AI 问答面板（经 Pi 代理）**：TUI `Ctrl+A` / Home「🤖 AI 问答」按钮 / `anote ask-pi "<问题>"`
  - 不直连 DeepSeek，而是调用 `pi -p`——Pi 自动加载 Anote 协议规则与记忆，按需 `anote ask --semantic` 检索知识库作答（实测：回答自动引用 `src/数学/代数/群论基础.tex`）
  - 异步执行不卡 UI；Markdown 渲染回答；显示耗时


## [0.9.0] - 2026-08-09（检索增强）

### 新增
- **全文搜索页**：TUI `Ctrl+F`（rg 集成，结果列表→F2 打开/F3 预览）；`context.rg()`
- **META 标签/学科过滤**：笔记页 F6 聚焦过滤框（匹配文件名+META 前 400 字）、F7 清除
- **模板系统**：`templates/note.tex` + `note-math.tex`（定理环境）；`anote new ... --template note|note-math`
- **每日笔记**：`anote daily`（src/日志/YYYY-MM-DD.tex，含当日队列快照）
- **可移植性强化**：setup.sh 装 anote 命令+定时器（单元文件归入项目 config/systemd/）；anote 脚本尊重 ANOTE_DATA env；venv 缺失回退 python3
- **AI 交接文档**：docs/HANDOFF.md（全部路径/命令/格式/决策/坑/可移植流程——新会话读它即可接手）

### 修复
- anote 脚本不尊重 ANOTE_DATA（bash 路径逻辑）；误建文件已清理


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

### 新增（P2 数据页实装）
- **Notes 笔记页**：学科树浏览/预览、新建（F2 弹窗）、编辑（$editor）、语义检索（F4 结果面板）
- **Queue 队列页**：表格渲染、状态切换（空格）、检索入队（F2）、打开笔记（F3）
- **Memory 记忆页**：四页签（日志/洞见/概念/问题）、追加条目（F2）
- **Books 书页**：书/章节列表、新建书·章（F2/F3）、编译（F4 输出面板）
- **Review 回顾页**：草稿列表/预览、一键生成（F2）
- **统一入口 `anote <命令>`**：tui/edit/new/search/ask/index/check/review/book/commit/backup/config；安装至 ~/.local/bin/anote；manage.sh 降为兼容包装
- **环境变量覆盖 `ANOTE_DATA`**：测试/临时切换数据目录无需改配置
- **集成测试**：test_smoke（8 屏导航）+ test_actions（5 项写操作，隔离临时目录）

### 新增（P3 + 统计）
- **数据迁移向导**：`scripts/migrate.py` + TUI 设置页接线（异步执行不卡 UI）；含 .git 随迁、文件数校验、失败回滚配置、--preview、--with-env 重建 venv；迁移日志 ~/.config/anote/migration.log
- **新手引导 Onboarding**：首次运行 3 步走完（首次真实运行出现，ANOTE_DATA 环境跳过）
- **文件统计**：`scripts/stats.py` + `anote stats`（笔记/论文/书/章/项目/回顾/队列/记忆条目/PDF/编译产物）；Home 仪表盘展示
- **功能路线图**：docs/ROADMAP.md（v0.9 检索增强 → v1.4 体验，参考 Pi/Obsidian/笔记软件）


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
