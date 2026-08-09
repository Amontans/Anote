# Anote 项目交接文档（AI 维护手册 · HANDOFF）

> **本文件是所有会话的"大脑"**：无论何时新开会话维护本项目，先读本文件 + `docs/INTERFACES.md` + `docs/ROADMAP.md`。
> 覆盖：项目全貌、全部路径、全部命令、数据格式、环境、决策、坑、可移植性。
> 最后更新：2026-08-09（v1.1.0 完成）

---

## 1. 项目是什么

**Anote**：个人科研知识库系统。纯 TEX 资产 + git 版本化 + AI（仅 DeepSeek）编排。
三级管线：`src/`（积累笔记）→ `memory/`（AI 编译记忆）→ `books/`（教科书成书）。
有 8 屏 TUI（Textual）+ 统一命令入口 `anote <command>` + 语义检索 + 数据迁移向导。

**用户核心约束（永远遵守）**：
1. AI 大模型只用 **DeepSeek**（用户已配置于 Pi）；不使用 Kimi/其他 LLM
2. 软件全开源、免订阅；数据 100% 本地纯文本，永不绑定专有工具
3. 正式文档用 **TEX**（数学/排版）；轻量数据（队列/记忆/状态）用 **MD/TXT**（不编译、免杂乱）
4. 数据目录可迁移（**含 .git 一起搬**）；编辑器可配置（code/vim/nvim/emacs/gedit/nano）
5. 项目（代码）与个人数据**分离存储**；数据目录拷到新电脑 = 无缝衔接

## 2. 关键路径总表

| 位置 | 内容 |
|------|------|
| `~/Projects/Anote/` | **项目**（代码+文档，git 仓库，MIT） |
| `~/Documents/Anote/` | **个人数据**（git 仓库，保留全部历史，推 gitee） |
| `~/.config/anote/config` | 配置（KEY=VALUE，bash/python 双解析） |
| `~/.config/anote/migration.log` | 迁移日志 |
| `~/.local/bin/anote` | 统一入口软链 → 项目 anote |
| `~/.config/systemd/user/notes-review.{service,timer}` | 周回顾定时器（周一 09:00） |
| `~/.pi/rules/academic-memory.md` | Pi 行为规则（指向 README 的 AI 协议） |
| `~/Documents/科研工作流大框架.md` | 用户主文档（框架 v3） |

## 3. 目录结构（项目）

```
~/Projects/Anote/
├── anote            # 统一入口（16 命令，见 §4）
├── manage.sh        # 兼容包装（exec anote）
├── setup.sh         # 一键自举（依赖/venv/索引/自检）
├── scripts/         # 12 个 Python 脚本（单一真相源）
│   ├── anote_config.py  # 配置读写（ANOTE_DATA env 可覆盖）
│   ├── search.py ask.py embed.py check.py review.py index-gen.py
│   ├── stats.py migrate.py daily.py fetch_paper.py extract.py
│   ├── bibclean.py new_paper.py
├── templates/       # 笔记/精读模板（note.tex, note-math.tex, reading-note.tex）
├── tui/             # Textual TUI（context/commands/app/screens×8/widgets/tests）
├── docs/            # ARCHITECTURE / INTERFACES / DEVELOPMENT / TUI-PLAN / ROADMAP / HANDOFF
├── README.md CHANGELOG.md LICENSE(MIT) VERSION
└── .gitignore
```

**数据目录**（`~/Documents/Anote/`）：`src/`（学科笔记+papers）、`memory/`（4 个 md+reviews）、`books/`、`projects/`、`queue.md`、`roadmap.md`、`refs.bib`、`pdfs/`、`.semantic/`（可重建）、`.venv/`（可重建）、`latexmkrc`、`.git/`（含 pre-commit hook）、`README.md`（数据目录说明）。

## 4. 统一入口命令（anote）

```
anote tui | edit <路径> | new <学科/分支> <标题> [--template 名]
     | search "<关键词>" | ask ["--smart"|"--semantic"] "<问题>"
     | index | index-semantic [--full] | check | stats | migrate --to <路径> [--preview|--force|--with-env]
     | review [--days N] | project <名> [目标] | book <书名> [作者] | chapter <书名> <章名>
     | book-build <书名> | commit [说明] | backup | config [set 键 值] | help
```
数据目录内可直接跑 `python3 ~/Projects/Anote/scripts/<脚本>.py ...`。

## 5. 数据格式契约（摘要；详见 docs/INTERFACES.md）

- **笔记**：`src/<学科>/<分支>/<日期>_<主题>.tex`，前 5 行内 META 块：
  `% ==META== 学科: X | 分支: Y | 标签: a,b | 日期: YYYY-MM-DD | 来源: 教材`
- **队列**：`queue.md` Markdown 表格（状态📥📖✅🗄 | 日期 | 论文 | ID | 笔记）
- **记忆层**：`memory/{research-log,insights,concepts,open-questions}.md`（## 日期 / - 条目）
- **配置键**：`data_dir editor lang semantic_model onboarded`
- **语义缓存**：`.semantic/chunks.json`（`{"schema_version":1,"chunks":[{path,mtime,text}]}`）+ `vectors.npy` float32 [N,512]
- **冻结层（永不破坏）**：src 笔记+META、memory 结构、queue 列结构。派生物（索引/缓存/回顾）可重建。

## 6. 环境与依赖

| 依赖 | 用途 | 检查 |
|------|------|------|
| latexmk/lualatex | 编译 TEX/书 | `latexmk --version` |
| pdftotext / ripgrep / git / python3 | 提取/检索/版本/脚本 | which |
| venv（数据目录 .venv） | fastembed/numpy/textual 8.2.8 | `~/Documents/Anote/.venv/bin/python` |

网络：WARP 代理 `socks5h://127.0.0.1:40000`（用户机器）；模型下载经 `HF_ENDPOINT=https://hf-mirror.com`（国内）。

## 7. 测试体系

```bash
cd ~/Projects/Anote
~/Documents/Anote/.venv/bin/python -m tui.test_smoke    # 8 屏导航
~/Documents/Anote/.venv/bin/python -m tui.test_actions  # 5 项写操作（临时目录隔离）
anote check                                              # 数据自检 6 项
```
测试隔离机制：`ANOTE_DATA` 环境变量覆盖数据目录（**绝不改配置文件**——早期踩过污染坑）。

## 8. 关键决策记录（含踩坑）

1. Textual 8.x：输入框聚焦会吞纯字母键 → 全局导航用 **Ctrl 组合键**（Ctrl+H/N/Q/M/B/R/S，F1 帮助，F5 自检，Ctrl+P 面板，Ctrl+D 退出）
2. `COMMANDS` 必须是列表 `[Provider]`
3. 长任务（迁移）用 `run_worker` + `create_subprocess_exec` 异步，防 UI 冻结
4. venv 是"可重建派生物"：迁移/换机后 `setup.sh` 或 `migrate --with-env` 重建
5. 测试不要改 config（用 env）；config 曾被污染导致级联失败（教训）
6. 脚本统一从 `anote_config.data_dir()` 读数据目录（默认 `~/Documents/Anote`）
7. 用户用 VS Code + Vim 编辑；`anote edit` 用配置的编辑器
8. 每周一 09:00 systemd 定时器自动生成回顾草稿

## 9. Pi 侧配置（已迁移到项目的部分）

- 4 个技能原在 `~/.pi/agent/skills/`，脚本已迁至项目 `scripts/`，SKILL.md 仅留文档并指向项目路径
- `~/.pi/rules/academic-memory.md`：会话记忆规则 + 指向 README 的 AI 操作协议
- Engram 记忆（mem_save）跨会话保存项目进展（搜索关键词：Anote）

## 10. 可移植性流程（换电脑无缝衔接）

```bash
# 新机器
git clone <Anote 项目仓库> ~/Projects/Anote      # 或拷整个目录
mkdir -p ~/Documents && cp -r <旧机数据> ~/Documents/Anote   # 拷数据目录（含 .git/.venv 可后建）
cd ~/Projects/Anote && ./setup.sh                # 依赖检查 + venv + 索引 + 自检 + 装 anote + 定时器
anote check                                       # 应全绿
anote index-semantic                              # 重建语义索引（若未随迁）
git -C ~/Documents/Anote remote add origin <gitee> && anote backup
```
**数据目录自足**：`~/Documents/Anote/README.md` 含完整说明；缺配置自动用默认值；venv/semantic 可重建。

## 11. 状态与待办

- 已完成：P0-P3（配置层/TUI 框架/数据页/迁移向导/引导/统计）；统一入口；语义检索；教科书层；测试；全文档
- **v1.1 完成**：AI 问答经 Pi（Ctrl+A / anote ask-pi）、反链（anote backlinks）、回顾自动化（weekly-review.sh 草稿+提交）、语义索引自动增量（pre-commit）
- **代码现代化**：src-layout 包（src/anote/）、薄适配器、单测 8 项；规范见 docs/CODING.md
- 下一步优先级：v1.1 AI 问答面板 → v0.9 完成 → v1.2 插件/MCP
- 未闭环：数据仓库 gitee 远程未配置（`anote backup` 只提交不推送）

## 12. 常见坑速查

| 现象 | 原因/解法 |
|------|-----------|
| `.venv/bin/pip: No such file` | venv 是移动来的，shebang 失效 → 删 .venv 重建（`setup.sh`） |
| 语义问答提示未建索引 | `anote index-semantic`（首次需 HF_ENDPOINT=hf-mirror） |
| TUI 输入框里按字母没反应/导航失效 | 导航必须用 Ctrl 组合（设计如此） |
| 迁移后 anote 找不到脚本 | 脚本在项目 `scripts/`，`anote` 用绝对路径 `~/Projects/Anote` |
| check 报 META 缺失 | 笔记前 5 行加 `% ==META==` 块 |
