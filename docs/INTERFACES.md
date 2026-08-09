# 接口契约文档（INTERFACES）

> 本文件是项目的"协议层"：**任何扩展、迁移、排查都以此为准，不需要读脚本代码**。
> 约定：所有路径默认 `~/Documents/Anote/`；所有文件 UTF-8；退出码 0=成功 1=失败（stderr 输出错误信息）。

---

## 1. 笔记文件接口（唯一真相源）

### 1.1 位置与命名
```
src/<学科>/<分支>/<YYYY-MM-DD>_<主题>.tex      # 学习笔记
src/papers/<YYYY-MM-DD>_<作者>_<主题>.tex      # 论文精读笔记
```
- 目录 = 学科分类骨架，**至少一层**（学科/），分支层数不限
- 每个含笔记的目录**必须**存在 `00-index.tex`（由 `index-gen.py` 自动生成，勿手改）

### 1.2 META 块（强制，前 5 行内）
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

**约束**：`check.py` 第 6 项校验 META 存在；缺 META 的文件会被标记。

### 1.3 真相源原则
`src/` 是**唯一不可再生的数据**。索引、语义缓存、队列、回顾全部可由 `src/` 重建。

---

## 2. 记忆层接口（memory/）

| 文件 | 条目格式 | 维护者 |
|------|----------|--------|
| `research-log.tex` | `\section*{YYYY-MM-DD}` + `\item 记录`（倒序） | AI（会话后） |
| `insights.tex` | 主题 `\section` + `\item 一句话洞见（来源标注）` | AI（回顾时） |
| `concepts.tex` | `\item \textbf{概念}：定义——来源` | AI（回顾时） |
| `open-questions.tex` | `\item 问题（背景/相关笔记/状态：开放\|解决中\|已解决+日期）` | AI（会话/回顾） |
| `reviews/review-*.tex` | 由 `review.py` 生成草稿，AI 填充，人确认 | 自动+AI |

---

## 3. 队列接口（queue.md）

- 表格列：`状态 | 日期 | 论文 | arXiv/DOI | 笔记路径`
- 状态机：`📥待读 → 📖在读 → ✅已精读 → 🗄已归档`（由 AI/脚本维护）
- 结构锚点：活动条目在 `% ===== 活动队列 =====` 标记之后；归档区在注释块中
- 一致性：`check.py` 第 2/3 项校验"✅ 必须有笔记"、"pdfs/ 内 PDF 必须有队列条目"

---

## 4. CLI 接口（scripts/*.py）

通用参数：`--notes <路径>`（默认 `~/Documents/Anote`）。输出一律 stdout，错误走 stderr。

| 脚本 | 输入参数 | 输出 | 退出码 |
|------|----------|------|:---:|
| `search.py` | `--provider arxiv\|s2\|openalex\|crossref` `--query` `--max N` `--since` `--since-months` `--sort` `--bib 文件` `--json 文件` `--queue 队列文件` `--doi` `--arxivid` `--papers "id1 id2"` `--citations` | 表格 + 摘要；`--bib`/`--json`/`--queue` 写文件 | 0 / 1 |
| `ask.py` | `query` `--smart` `--semantic` `--top N` `--maxchars N` | 命中片段（带文件路径+行号）或语义 top-k（带相似度） | 0 / 1（未建语义索引=1） |
| `embed.py` | `--full`（全量重建） | 写 `.semantic/chunks.json` + `vectors.npy`；增量跳过未变更 | 0 |
| `index-gen.py` | （无） | 重写所有 `00-index.tex`（含嵌套 `\input`） | 0 |
| `check.py` | （无） | 6 项检查报告（stdout），问题在 `⚠️` 行 | 0（始终） |
| `review.py` | `--days N` `--since` `--out` | 写 `memory/reviews/review-*.tex` 草稿 | 0 |
| `fetch_paper.py` | `--arxivid` `--doi` `--url` `--dir` `--no-extract` `--tex-note [目录]` | 下载 PDF + 提取 `.txt` + 可选生成 TEX 笔记 | 0 / 1 |
| `extract.py` | `pdf` `--out` | 写 `.txt` | 0 / 1 |
| `bibclean.py` | `bib` `--dedupe` `--sort` `--out` | 重写 bib 文件 | 0 |
| `new_paper.py` | `name` `--lang` `--fmt latex\|md` `--author` `--dir` | 生成论文骨架 | 0 |

---

## 5. 语义缓存接口（.semantic/）

```json
// chunks.json
{ "schema_version": 1,
  "chunks": [ { "path": "绝对路径", "mtime": 1234.56, "text": "切块文本" } ] }
```
- `vectors.npy`：`float32 [N, 512]`，第 i 行对应 chunks[i]（bge-small-zh-v1.5，512 维）
- **可重建**：删除 `.semantic/` 后 `anote index-semantic` 全量重建，无数据损失
- **演进规则**：`schema_version` 变更 = 缓存格式不兼容，脚本需做迁移或自动全量重建

---

## 6. 命令接口（manage.sh —— 唯一入口）

```
notes {index | index-semantic [--full] | check | review [--days N] | ask [--smart|--semantic] "问题"
      | new <学科/分支> <标题> | project <名> [目标] | book <书名> [作者]
      | chapter <书名> <章名> | book-build <书名> | commit [说明] | backup | all}
```
- 所有命令幂等；`commit` 触发 pre-commit hook
- 新增命令必须：① 在此列表注册 ② 遵循通用参数约定 ③ 更新 `docs/EXTENDING.md`

---

## 7. git 钩子接口

| 钩子 | 行为契约 |
|------|----------|
| `pre-commit` | ① 自动重跑 `index-gen.py` 并纳入提交 ② 运行 `check.py` 打印提示（**不阻断**） |

---

## 8. 升级接口（向后兼容策略）

- **数据格式冻结层**：`src/`、`memory/`、`queue.md` 的格式 = v1 契约，**永不破坏性变更**；新增字段必须可选项
- **派生物可重建**：`.semantic/`、`00-index.tex`、`reviews/` 变更 schema 时自动重建，无需迁移
- **脚本接口**：新增参数必须带默认值（= 旧行为）；删参数需先弃用一个版本
- 具体版本历史见 `docs/UPGRADING.md`
