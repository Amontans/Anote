# 生态插件兼容性分析（ECOSYSTEM-COMPAT）

> 问题：能否兼容 Zotero / Obsidian 等软件的插件？
> 结论先行：**插件不能"直接运行"（运行时绑定各自应用），但"数据生态"可以最大化兼容**——我们的文件已是它们的母语。

## 一、关键认知：插件 = 绑定运行时

| 生态 | 插件运行环境 | 依赖的私有 API |
|------|--------------|----------------|
| Zotero 插件（.xpi） | 必须在 Zotero 内 | zotero.sqlite、Zotero 内部对象、translators |
| Obsidian 插件（JS） | 必须在 Obsidian 内 | Vault API、plugin API、渲染管线 |
| Joplin/Logseq 插件 | 各自应用内 | 各自私有格式 |

**Anote 无法运行这些插件**（不同运行时、不同语言/API）——这与"Obsidian 不能运行 VS Code 扩展"同理。强行移植 = 重写，违背低维护原则。

## 二、但我们能兼容的：三层

### 第 1 层：数据格式原生互通（已经在发生，最值钱）
Anote 的文件全部是**标准格式** → 那些生态的"查看/编辑/插件"天然作用于我们的数据：

| 我们的数据 | 标准格式 | 可被谁原生使用（含其插件生态） |
|-----------|----------|------------------------------|
| memory/ registry.md queue.md | **Markdown** | Obsidian（含 Dataview 等全部插件）、Joplin、Logseq、VS Code、Typora |
| src/ books/（TEX） | **LaTeX** | VS Code + LaTeX Workshop、vimtex、Overleaf（全部 LaTeX 生态） |
| refs.bib | **BibTeX** | Zotero/Better BibTeX、JabRef |
| pdfs/ ebooks/ | **PDF/epub** | Zotero 内置阅读器、Foliate、Calibre、KOReader |

> 例：把 `~/Documents/Anote/memory` 作为 Obsidian vault 打开 → **Obsidian 的 2000+ 插件（Dataview 仪表盘、图谱、模板）直接可用**，无需我们做任何事。

### 第 2 层：导入器（消费它们产出的数据）
插件们产出的**标准数据**，Anote 可以导入：

| 来源 | 产出 | 导入方式 | 状态 |
|------|------|----------|:---:|
| Zotero 标注导出 | Markdown 标注文件 | `anote docs annotations` → 并入精读笔记 | 规划(M4) |
| Better BibTeX | refs.bib | 已有 ✅ | 完成 |
| Obsidian vault 导出 | .md 笔记 | `anote import-md <目录>` → src/ 或 memory/ | 可做 |
| Logseq/Joplin 导出 | .md | 同上（通用 MD 导入） | 可做 |
| Zotero 整库 | CSL JSON / RDF | `anote zotero bib`（bib 已支持） | 部分 |

### 第 3 层：桥接（让别的工具能调用 Anote）
| 桥 | 现状 |
|----|:---:|
| **MCP Server**（`anote mcp`） | ✅ 已实现——Claude/Cursor/其他 AI 工具可调 Anote 全部能力 |
| CLI 命令 | ✅——Obsidian 用户可用社区插件"Shell commands"在笔记里执行 `anote ask ...`；VS Code 任务可调 |
| **VS Code Anote 扩展**（可选 A1） | 待做——把 docs/registry/检索做成侧边栏 |

## 三、其他可兼容的生态（汇总）

| 生态 | 兼容方式 | 价值 |
|------|----------|:---:|
| **VS Code 扩展** | 我们的 TEX/MD 是其母语 → LaTeX Workshop 等全部可用 | ⭐⭐⭐ |
| **Neovim 插件** | 同上（vimtex/telescope/markdown） | ⭐⭐⭐ |
| **Obsidian 插件** | 把 memory/ 当 vault 打开 → Dataview/图谱/模板 | ⭐⭐（MD 层） |
| **Zotero 插件** | 消费导出数据（BibTeX/标注） | ⭐⭐⭐ |
| **MCP 生态** | 我们已是 server；其他 server 可选接入 | ⭐⭐ |
| **JabRef** | refs.bib 双向 | ⭐（备选） |
| **KOReader/Calibre** | epub/pdf 阅读（进度可回传） | ⭐⭐ |

## 四、最大化兼容的实施计划（按价值排序）

| 优先 | 项 | 工作量 |
|:---:|----|:---:|
| P0 | **通用 MD 导入** `anote import-md <目录>`（Obsidian/Logseq/Joplin 导出的 .md → 按 META 或目录映射进 src/） | 半天 |
| P0 | **Zotero 标注导入** `anote docs annotations <标注.md>`（并入精读笔记） | 半天 |
| P1 | **VS Code 扩展**（A1：侧边栏文档表格/笔记树/检索）——把 VS Code 变成 Anote 的"GUI" | 几天 |
| P1 | **Obsidian 桥接文档**：README 说明如何把 memory/ 当 vault（含 Dataview 示例仪表盘） | 半天 |
| P2 | 导出增强：`anote export --md`（知识库 → 纯 MD 站，供 Obsidian/静态站） | 半天 |
| P2 | 其他 MCP server 接入（如让 anote 调用外部搜索 MCP） | 视需要 |

## 五、边界（诚实说明）
- ❌ 不承诺"运行 Zotero/Obsidian 插件"（架构上不可能且没必要）
- ✅ 承诺：**任何产生标准格式数据的插件，Anote 都能导入/导出互通**
- 原则不变：我们的核心仍是 TEX+MD 纯文本 + services；兼容层只是"进口/出口"和"桥"

## 六、待你选择
1. 先做 **P0 两个导入器**（MD 导入 + Zotero 标注导入）？
2. 还是先做 **P1 VS Code 扩展**（把 VS Code 变成 GUI 感最强的一环）？
3. 或者先写 **Obsidian 桥接文档**（零代码，立刻可用 Dataview 仪表盘）？
