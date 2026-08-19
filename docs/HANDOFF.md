# Anote 项目交接文档（AI 维护手册 · HANDOFF）

> **文档导航（AI 视角，按需读）**：
> ① 本文件（交接总纲）→ ② `docs/INTERFACES.md`（契约）→ ③ `docs/CODING.md`（规范）
> 用户侧文档：`README.md`（入口）+ `docs/USER-GUIDE.md`（手册）
> 规划：`docs/ROADMAP.md`；历史决策在 `docs/archive/`

> **本文件是所有会话的"大脑"**：新开会话维护本项目，先读本文件 + `docs/INTERFACES.md` + `docs/ROADMAP.md`。
> 最后更新：2026-08-19（v1.16.0：数据根可在设置中修改并自动迁移；BM25 倒排索引持久化；命令注册表）

---

## 1. 项目是什么

**Anote**：个人科研知识库系统。纯 TEX/MD 资产 + git 版本化 + AI（仅 DeepSeek，经 Pi）编排。
三级管线：`src/`（积累笔记）→ `memory/`（AI 编译记忆）→ `books/`（教科书成书）。
有 TUI（Textual）+ 统一命令入口 `anote <command>` + 混合语义检索 + 数据迁移向导。

**用户核心约束（永远遵守）**：
1. AI 大模型只用 **DeepSeek**（经 Pi 代理）；默认不使用其他 LLM
2. 软件全开源、免订阅；数据 100% 本地纯文本，永不绑定专有工具
3. 正式文档用 **TEX**；轻量数据（队列/记忆/状态）用 **MD**
4. 数据根可迁移（**含 .git 与 .anote 配置一起搬**）
5. 项目（代码）与个人数据**分离**；除数据根外不写用户数据

## 2. 关键路径总表

| 位置 | 内容 |
|------|------|
| `<项目目录>/` | 代码+文档（git 仓库，MIT）。**不含用户数据，可直接上传 GitHub** |
| `<数据根>/` | 唯一用户数据位置（默认 `~/Documents/Anote`，`ANOTE_DATA` 可覆盖） |
| `<数据根>/.anote/config` | 配置（KEY=VALUE；bash/python 双解析） |
| `<数据根>/.anote/logs/` | 运行日志 |
| `<数据根>/.anote/external.json` | 外部 MCP server 注册 |
| `<数据根>/.anote/migration.log` | 迁移日志 |
| `<数据根>/.anote/backups/` | 默认备份输出（可 `--out` 外置冷备） |
| `~/.config/anote/config` | **数据根定位指针**（仅一行 `data_dir=`）；TUI 设置保存/迁移后自动更新 |

项目路径无需固定：`anote`、`setup.sh`、shell 脚本全部从自身位置推导；
systemd 单元安装时把 `@@PROJECT@@` 替换为实际项目路径。

## 3. 目录结构（项目）

```
<项目根>/
├── anote            # 统一入口（40+ 命令，路径自动推导）
├── manage.sh        # 兼容包装（exec anote）
├── setup.sh         # 一键自举（数据骨架/git/venv/索引/hook/定时器/命令）
├── scripts/         # 42 个 Python + 4 个 shell 薄适配器（含 init_data/new/fetch_paper）
├── src/anote/       # core.py + services/ 包（22 领域，重模块按需加载）
├── templates/       # note / note-math / reading-note / book / project 模板
├── config/          # systemd 模板（@@PROJECT@@）+ git-hooks 模板
├── tui/             # Textual TUI（11 屏 + widgets + 双测试）
├── tests/           # 单元/集成测试
├── docs/            # 文档
└── README.md CHANGELOG.md LICENSE VERSION .gitignore
```

**数据根**：`src/`、`memory/`、`books/`、`projects/`、`docs/registry.md`、`queue.md`、`roadmap.md`、`refs.bib`、`pdfs/`、`ebooks/`、`.anote/`、`.semantic/`（可重建）、`.venv/`（可重建）、`.git/`（含 pre-commit/pre-push）。

## 4. 统一入口命令（anote）

```
anote tui | edit <路径> | new <学科/分支> <标题> [--template 名] [--no-edit]
     | daily | search | ask [--semantic] | ask-pi | ai "<自然语言>"
     | index | index-semantic [--full] | check [--strict] | stats
     | migrate --to <路径> [--preview|--force|--with-env] | init-data
     | review [--days N] | project <名> [目标] | book <书名> [作者]
     | chapter <书名> <章名> | book-build <书名>
     | read <路径> | docs {list|add|update|progress|stats|import|annotations}
     | paper <主题> | wiki | meta | graph | report | backlinks
     | zotero {status|bib|setup} | bibcheck | bibclean | convert | ebook | index-pdf
     | backup-create [--encrypt] | restore <文件> | archive <年份>
     | web [--port N] | export [--out 路径] | mcp | external {list|call}
     | plugin {list|add|run} | lint | md | preview | checklist | eval
     | commit [说明] | backup | config [set 键 值] | test | release | help
```
数据根内可直接跑 `python3 <项目>/scripts/<脚本>.py ...`（建议带 `ANOTE_DATA`）。

## 5. 数据格式契约（摘要；详见 docs/INTERFACES.md）

- **笔记**：`src/<学科>/<分支>/<日期>_<主题>.tex`，前 5 行内 META 块：
  `% ==META== 学科: X | 分支: Y | 标签: a,b | 日期: YYYY-MM-DD | 来源: 教材`
- **队列**：`queue.md` Markdown 表格（状态📥📖✅🗄 | 日期 | 论文 | ID | 笔记）
- **记忆层**：`memory/{research-log,insights,concepts,open-questions}.md`（## 日期 / - 条目）
- **配置键**：`data_dir editor lang semantic_model onboarded ai_provider pi_bin theme reader`
- **语义缓存**：`.semantic/chunks.json`（`{"schema_version":1,"chunks":[{path,mtime,text}]}`）+ `vectors.npy` float32 [N,512]
- **冻结层（永不破坏）**：src 笔记+META、memory 结构、queue 列结构。派生物（索引/缓存/回顾）可重建。

## 6. 环境与依赖

| 依赖 | 用途 | 检查 |
|------|------|------|
| latexmk/lualatex | 编译 TEX/书 | `latexmk --version` |
| pdftotext / ripgrep / git / python3 | 提取/检索/版本/脚本 | which |
| venv（数据根 .venv） | fastembed/numpy/textual/fastmcp | `<数据根>/.venv/bin/python` |

网络：模型下载经 `HF_ENDPOINT=https://hf-mirror.com`（国内）。

## 7. 测试体系

```bash
cd <项目根>
<数据根>/.venv/bin/python -m unittest discover -s tests   # 20 项（MCP 无 fastembed 自动跳过）
<数据根>/.venv/bin/python -m tui.test_smoke               # 11 屏导航
<数据根>/.venv/bin/python -m tui.test_actions             # 5 项写操作（临时目录隔离）
anote check --strict                                      # 数据自检 8 项（发现警告返回 1）
anote test                                                # 一键门禁（上面四件套）
```
测试隔离机制：`ANOTE_DATA` 环境变量覆盖数据根（**绝不改配置文件**）。

## 8. 关键决策记录（含踩坑）

1. **v1.16 数据自足**：所有用户数据（配置/日志/MCP注册/迁移日志/默认备份/预览）统一放数据根 `.anote/`；旧 `~/.config/anote/config` 的完整配置首次读取时迁入数据根，随后该文件只保留一行 `data_dir=` 定位指针；TUI 设置页直接修改“数据目录”保存即自动迁移。项目仓库因此不含任何用户数据，可直接上传 GitHub。
2. **项目路径自动推导**：`anote` 跟随符号链接解析自身位置；`setup.sh`/测试脚本同理。systemd 单元用 `@@PROJECT@@` 占位，安装时 sed 替换。早期硬编码 `~/Projects/Anote`、`/home/Amontans` 的坑已清除。
3. **配置与数据根解耦**：`data_dir` 不再直接 `config set`，只能 `anote migrate --to`。`ANOTE_DATA` 是测试隔离硬边界（不读旧配置）。
4. **同名笔记绝不覆盖**：`anote new` 用 Python 模板替换（避免 sed `&` 注入）并做 LaTeX 转义；已存在时退出 1。
5. **MCP 离线可用**：`mcp.run(show_banner=False)`，避免 FastMCP banner 联网检查 PyPI 导致离线崩溃。
6. **Textual 8.x**：输入框聚焦会吞纯字母键 → 全局导航用 **Ctrl 组合键**。
7. **日志不阻断命令**：`setup_logging()` 写入数据根 `.anote/logs`；不可写时降级 stderr，绝不因日志失败拖垮 CLI。
8. **测试不碰真实数据**：TUI 测试用 `bootstrap.ensure_data_dir(TMP)` 自建模板，不再依赖真实数据目录。
9. **venv/.semantic 是"可重建派生物"**：迁移/换机后 `setup.sh` 或 `migrate --with-env` 重建。
10. **check 8 项**：`--strict` 供门禁返回非零；默认只报告。PDF 只要在 queue 或 registry 之一登记即不算孤儿。

## 9. 可移植性流程（换电脑无缝衔接）

```bash
# 新机器（项目目录任意路径）
git clone <Anote 项目仓库> <项目>                # 或拷整个目录（无用户数据，可上传 GitHub）
cp -r <旧机数据根> ~/Documents/Anote              # 含 .git 与 .anote 一起搬
cd <项目> && ./setup.sh                           # 骨架/venv/索引/hook/定时器/安装 anote
anote check --strict                              # 应全绿
anote index-semantic                              # 重建语义索引（若未随迁）
git -C ~/Documents/Anote remote add origin <gitee> && anote backup
```
**数据根自足**：`<数据根>/README.md` 与 `.anote/config` 都在数据根内；缺配置自动用默认值；venv/semantic 可重建。

## 10. 常见坑速查

| 现象 | 原因/解法 |
|------|-----------|
| `.venv/bin/pip: No such file` | venv 是移动来的，shebang 失效 → 删 .venv 重跑 `setup.sh` |
| 语义问答提示未建索引 | `anote index-semantic`（首次需 HF_ENDPOINT=hf-mirror） |
| TUI 输入框里按字母没反应 | 导航必须用 Ctrl 组合（设计如此） |
| `anote config set data_dir` 报错 | 正确方式：`anote migrate --to <新路径>` |
| check 报 META 缺失 | 笔记前 5 行加 `% ==META==` 块 |
| check [1] 报缺 00-index | `anote index` 生成分层索引 |
| 旧 `~/.config/anote/config` 仍有完整配置 | 运行一次 `anote config`，会自动把完整配置迁入数据根，旧文件只保留 data_dir 指针 |
