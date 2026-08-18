# 接口契约文档（INTERFACES）

> 本文件是项目的"协议层"：**任何扩展、迁移、排查都以此为准，不需要读脚本代码**。
> 约定：路径默认 `<数据根>/`（默认 `~/Documents/Anote`，`ANOTE_DATA` 可覆盖）；所有文件 UTF-8；退出码 0=成功 1=失败（stderr 输出错误信息）。

---

## 1. 数据根与运行目录（v1.15）

| 路径 | 内容 | 是否随迁/备份 |
|------|------|:---:|
| `src/` | ★ 学习笔记（唯一真相源） | ✅ |
| `memory/` | 记忆层（MD） | ✅ |
| `books/` `projects/` | 教科书 / 项目 | ✅ |
| `pdfs/` `ebooks/` | 文档附件 | ✅（目录拷贝；git 默认忽略 pdfs/） |
| `docs/registry.md` | 文档登记表 | ✅ |
| `queue.md` `roadmap.md` `refs.bib` | 队列/路线图/引用库 | ✅ |
| `.anote/config` | 配置（KEY=VALUE） | ✅ |
| `.anote/external.json` | 外部 MCP server 注册 | ✅ |
| `.anote/logs/` `.anote/previews/` | 运行日志/预览缓存 | ❌ 可重建 |
| `.anote/migration.log` | 迁移日志 | ❌ 可重建 |
| `.anote/backups/` `.anote/exports/` | 默认备份/导出输出 | ❌ 派生物 |
| `.semantic/` `.venv/` | 语义缓存/依赖 | ❌ 可重建 |

规则：**除数据根外不写任何用户数据**。旧 `~/.config/anote/config` 是 v1.14 遗留指针，
首次读取后自动复制到 `.anote/config` 并删除（删除失败时保留但不再作为写入位置）。

## 2. 笔记文件接口（唯一真相源）

### 2.1 位置与命名
```
src/<学科>/<分支>/<YYYY-MM-DD>_<主题>.tex      # 学习笔记
src/papers/<YYYY-MM-DD>_<作者/ID>_<主题>.tex    # 论文精读笔记
```
- 目录 = 学科分类骨架，**至少一层**（学科/），分支层数不限
- 每个含笔记的目录**必须**存在 `00-index.tex`（由 `index-gen.py` 生成，勿手改；check [1] 会同时校验"目录缺索引"与"笔记未登记"）
- `src/_archive/` 与所有 `_`/`.` 开头目录自动排除在笔记扫描与语义索引外

### 2.2 META 块（强制，前 5 行内）
```latex
% ==META== 学科: 数学 | 分支: 代数 | 标签: 群论,环论 | 日期: 2026-08-09 | 来源: 教材
```
| 字段 | 必填 | 取值 |
|------|:---:|------|
| `学科` | ✅ | 任意字符串（建议与目录对应） |
| `分支` | 否 | 子学科名 |
| `标签` | 否 | 逗号分隔，用于跨学科检索 |
| `日期` | ✅ | `YYYY-MM-DD` |
| `来源` | 否 | 教材 / 论文 / 其他 |

### 2.3 真相源原则
`src/` 是**唯一不可再生的数据**。索引、语义缓存、队列、回顾全部可由 `src/` 重建。

---

## 3. 记忆层接口（memory/，MD）

| 文件 | 条目格式 | 维护者 |
|------|----------|--------|
| `research-log.md` | `## YYYY-MM-DD` + `- 记录`（倒序） | AI（会话后） |
| `insights.md` | `## 主题` + `- 一句话洞见（来源标注）` | AI（回顾时） |
| `concepts.md` | `## 主题` + `- **概念**：定义——来源` | AI（回顾时） |
| `open-questions.md` | `## 主题` + `- 问题（背景/相关笔记/状态：开放\|解决中\|已解决+日期）` | AI（会话/回顾） |
| `reviews/review-*.md` | 由 `review.py` 生成草稿，AI 填充，人确认 | 自动+AI |
| `reports/*.md` | `anote report` 周报 | 自动 |

---

## 4. 队列接口（queue.md）

- 表格列：`状态 | 日期 | 论文 | arXiv/DOI | 笔记`
- 状态机：`📥待读 → 📖在读 → ✅已精读 → 🗄已归档`（由 AI/脚本维护）
- 入队规则：若文件含注释 `<!-- 活动队列 -->`，新行插入该标记后；否则插入表头分隔行后
- 一致性：check [2] 校验"✅ 必须有笔记"；check [3] 校验 PDF 至少在 queue 或 registry 之一登记

---

## 5. CLI 接口（scripts/*.py）

通用规则：数据根经 `ANOTE_DATA` 或默认目录解析；输出 stdout，错误 stderr。

| 脚本 | 输入参数 | 输出 | 退出码 |
|------|----------|------|:---:|
| `search.py` | `--provider arxiv\|s2\|openalex\|crossref --query --max --bib --json --queue --doi --arxivid --papers --citations` | 结果表 + 可选写 bib/json/queue | 0/1 |
| `ask.py` | `query [--smart] [--semantic] [--bm25] [--top N] [--maxchars N] [--layer notes\|docs]` | 命中片段/混合检索 top-k | 0/1 |
| `embed.py` | `[--full]` | 写 `.semantic/chunks.json` + `vectors.npy`；增量跳过未变更 | 0 |
| `index-gen.py` | 无 | 重写所有 `00-index.tex` | 0 |
| `check.py` | `[--strict]` | 8 项检查报告；`--strict` 有警告时退出 1 | 0/1 |
| `review.py` | `--days N --out 路径` | 写 `memory/reviews/review-*.md` 草稿 | 0 |
| `fetch_paper.py` | `--arxivid --doi --url [--dir 目录] [--no-extract] [--tex-note [目录]]` | 下载 PDF（默认数据根 pdfs/）+ 提取 + 可选 TEX 笔记（含 META） | 0/1 |
| `new.py` | `<学科/分支> <标题> [--template note\|note-math] [--no-edit]` | 新建笔记；已存在不覆盖 | 0/1 |
| `init_data.py` | 无 | 幂等初始化数据根骨架 | 0 |
| `bibcheck.py` | 无 | 引用链路报告 | 0/1 |
| `migrate.py` | `--to 路径 [--preview --force --no-config --with-env]` | 迁移数据根（含 .git/.anote 配置，校验回滚） | 0/1 |
| `stats.py` | `[--json]` | 各类文件数 | 0 |
| `backlinks.py` | `<概念> [--json]` | 反链视图（rg 计数 + META 标签） | 0 |
| `backup.py` | `[--out 目录] [--encrypt] [--no-git]` | 默认写 `.anote/backups/`；含 .sha256；排除运行产物 | 0/1 |
| `restore.py` | `<备份> [--dry-run --force --to --key]` | 校验和 + 安全解包（拒绝路径穿越/特殊文件） | 0/1 |
| `export.py` | `[--out 路径] [--with-git]` | 默认写 `.anote/exports/` | 0/1 |

---

## 6. 语义缓存接口（.semantic/）

```json
// chunks.json
{ "schema_version": 1,
  "chunks": [ { "path": "绝对路径", "mtime": 1234.56, "text": "切块文本" } ] }
```
- `vectors.npy`：`float32 [N, 512]`，第 i 行对应 chunks[i]（默认 bge-small-zh-v1.5；`.anote/config` 的 `semantic_model` 生效）
- **可重建**：删除 `.semantic/` 后 `anote index-semantic` 全量重建
- **演进规则**：`schema_version` 变更 = 缓存格式不兼容，脚本需做迁移或自动全量重建

---

## 7. 命令接口（anote —— 唯一入口）

```
anote {tui|edit|new|daily|search|ask|ask-pi|ai|index|index-semantic|check|stats|
       migrate|init-data|review|project|book|chapter|book-build|read|docs|paper|
       wiki|meta|graph|report|backlinks|zotero|bibcheck|bibclean|convert|ebook|
       index-pdf|backup-create|restore|archive|web|export|mcp|external|plugin|lint|
       md|preview|checklist|eval|commit|backup|config|test|release|help}
```
- 所有命令幂等（除 new/paper 等显式创建）；`commit` 自动索引+自检+提交
- `manage.sh` 仅为兼容包装：`exec anote "$@"`

## 8. git 钩子接口

| 钩子 | 行为契约 |
|------|----------|
| `pre-commit` | ① 自动重跑 `index-gen.py` 并纳入提交 ② 运行 `check.py` 打印提示（不阻断） |
| `pre-push` | 运行 `anote test`，失败阻断推送 |

钩子模板在项目 `config/git-hooks/`，`setup.sh` 安装到数据根 `.git/hooks/`；内容不写死项目路径，只依赖 PATH 中的 `anote`。

## 9. 文档登记契约（docs/registry.md）

表格列：`状态 | 类型 | 文件 | 标题 | 作者 | 年份 | 标签 | 笔记 | 进度 | 最后阅读 | 哈希`
- 状态机：📥待读 → 📖在读 → ✅读完 → 🗄归档（与 queue.md 对齐）
- 文件 = 相对数据根路径；哈希 = sha256 前 8 位（去重键）
- 派生产物（pdfs/*.txt）不登记、不被 check 标记
- 维护：`anote docs {list|add|update|progress|stats|import}`；`anote read` 读即登记

## 10. 升级接口（向后兼容策略）

- **数据格式冻结层**：`src/`、`memory/`、`queue.md` 的格式 = v1 契约，**永不破坏性变更**；新增字段必须可选项
- **派生物可重建**：`.semantic/`、`00-index.tex`、`reviews/`、`.anote/logs` 变更 schema 时自动重建
- **脚本接口**：新增参数必须带默认值（= 旧行为）；删参数需先弃用一个版本
- 版本历史见 `CHANGELOG.md`；扩展规范见 `docs/CODING.md`
