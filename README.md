# 科研知识库系统（Research Knowledge OS）

> 长期科研"操作系统"：纯 TEX 资产 + git 版本化 + AI（DeepSeek）编排。**自足运行：任何 AI 助手读本文档 + `docs/` 即可独立答疑与辅助学习，无需额外背景。**

**版本**: 0.6.0 · **协议**: MIT · **依赖**: latexmk / pdftotext / ripgrep / git / python3（语义检索需 fastembed+numpy，可选）

## 快速开始

```bash
cd ~/Projects/Anote
./setup.sh          # 一键自举（依赖检查+venv+索引+自检，幂等）
alias notes="$PWD/manage.sh"

anote new 数学/代数 "标题"          # 新建笔记（自动 META 模板）
anote ask "关键词"                  # 问答（grep 模式）
anote ask --semantic "自然语言问题"  # 问答（语义模式）
anote commit "说明"                 # 提交（自动索引+自检）
anote review --days 7              # 周回顾
anote book "书名" && anote book-build "书名"   # 开写/编译教科书
anote backup                        # 提交+推送远程
```

## AI 助手操作协议（本系统自足运行的关键）

> 任何 AI 助手（Pi 或其他）**只需要本文件 + `docs/` 即可上岗**。协议如下：

### 角色定位
- **你负责**：阅读 `docs/INTERFACES.md`（数据格式契约）与 `docs/ARCHITECTURE.md`（数据流）后，回答用户的疑问、辅助学习。
- **用户负责**：写笔记内容、确认 AI 的提炼与建议、定方向。
- **数据主权**：`src/` 是唯一真相源，AI 只增改经用户确认的内容。

### 用户提问时（答疑）
1. 知识库内的问题 → 先跑 `anote ask --semantic "<问题>"`；语义结果不足时 `anote ask "<关键词>"`；仍不足再直接读 `src/` 下相关文件。
2. 需要引原文/出处 → 报告 `ask` 输出的文件路径，不臆造。
3. 学术概念/写作类 → 结合 `memory/concepts.tex`、`docs/` 与网络检索回答。

### 用户要学习辅助时
- **找文献**：`scripts/search.py --provider arxiv|openalex|s2|crossref --query "..." --queue ~/Documents/Anote/queue.md`
- **读论文**：`scripts/fetch_paper.py --arxivid <ID> --tex-note` → 读提取文本 → 按模板填充 → 更新队列状态（📖→✅）
- **沉淀知识**：会话结束更新 `memory/research-log.tex`；有影响思考的结论写 `insights.tex`；矛盾/未解写 `open-questions.tex`（格式见 INTERFACES §2）
- **周回顾**：`anote review --days 7` → 提炼洞见/概念 → 用户确认 → commit
- **写教科书**：`anote book/chapter/book-build` 全流程

### 红线
- 不直接修改 `src/` 笔记的语义内容（可经 `anote new` 建模板、经用户同意后填充）。
- 不破坏 INTERFACES.md 定义的任何格式。
- 所有变更经 `anote commit` 提交（pre-commit 自动索引+自检）。

## 目录结构与用途（每个文件的说明）

### 🚪 入口（你只碰这些）
| 文件 | 作用 | 怎么用 |
|------|------|--------|
| `manage.sh` | **唯一命令入口** | `anote <命令>`（建议 `alias notes="~/Projects/Anote/manage.sh"`） |
| `setup.sh` | 一键自举/重建系统 | 新机器或损坏后运行一次，幂等 |

### 📚 文档（先读这些）
| 文件 | 作用 |
|------|------|
| `README.md` | 本文件：总览 + AI 操作协议 |
| `docs/ARCHITECTURE.md` | 架构、分层、数据流 |
| `docs/INTERFACES.md` | **全部数据格式与命令接口契约**（扩展/排查的依据） |
| `docs/DEVELOPMENT.md` | 扩展检查清单 + 升级路径 |
| `CHANGELOG.md` `LICENSE` `VERSION` | 版本历史 / MIT 许可 / 当前版本 |

### 🧠 知识数据（你的资产，全部纯文本）
| 路径 | 作用 | 怎么用 |
|------|------|--------|
| `src/<学科>/<分支>/*.tex` | **唯一真相源**：学习笔记（META 头） | `anote new 学科/分支 "标题"` 起步，VS Code/Vim 写 |
| `src/papers/` | 论文精读笔记 | `fetch_paper.py --arxivid <ID> --tex-note` |
| `memory/` | 记忆层：研究日志/洞见/概念/开放问题/回顾 | AI 自动维护，你每周确认 |
| `books/<书名>/` | 教科书（ctexbook 项目） | `anote book / chapter / book-build` |
| `projects/<名>/` | 研究项目（plan+log） | `anote project "名" "目标"` |
| `queue.md` | 论文待读队列（📥→📖→✅→🗄） | `search.py --queue` 入队，AI 更新状态 |
| `roadmap.tex` | 研究路线图（季度审视） | 月度回顾时更新 |
| `refs.bib` | 引用库 | Zotero/JabRef 导出，`\cite{}` 引用 |
| `pdfs/` | PDF 附件（不入 git） | 下载的论文放这 |

### ⚙️ 内部（一般不用碰）
| 路径 | 作用 |
|------|------|
| `scripts/` | 10 个 Python 脚本（search/ask/embed/check/review/index-gen/…）——被 manage.sh 调用 |
| `templates/` | 笔记/精读模板 |
| `latexmkrc` | 编译配置（lualatex+中文） |
| `.semantic/` | 语义索引缓存（可删可重建） |
| `.venv/` | Python 环境（语义检索用） |

## 文档索引（先读这些，不用读代码）

| 文档 | 内容 |
|------|------|
| `docs/ARCHITECTURE.md` | 架构、分层、数据流、设计原则 |
| `docs/INTERFACES.md` | **全部输入输出接口契约**（格式/CLI/缓存/钩子/升级策略） |
| `docs/DEVELOPMENT.md` | 扩展指南 + 升级路径（不读代码的检查清单） |

## 故障速查

| 症状 | 修复 |
|------|------|
| check 报错 | 按提示处理（缺 META→加头；未登记→anote index；PDF 孤儿→补队列行或删文件） |
| 语义问答提示未建索引 | `anote index-semantic` |
| 误删文件 | `git log --oneline` → `git checkout <commit> -- <file>` |
| 语义缓存坏了 | `rm -rf .semantic && anote index-semantic` |
| 系统整体损坏 | `./setup.sh` 自举重建（src/ 无损） |

## 版本

见 `CHANGELOG.md`（当前 0.6.0）。升级与兼容承诺见 `docs/DEVELOPMENT.md`。
