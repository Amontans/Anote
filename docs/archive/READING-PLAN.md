# 阅读与管理升级规划（READING-PLAN）

> 目标：**良好的手动阅读环境 + 极佳的管理**。约束：本地优先、开源、AI 仅经 Pi、8GB 轻量、数据可移植、冻结层不破坏。
> 状态：M1-M3 已完成（v1.10.0）；M4/M5 待做。

## 〇、分工原则（先定哲学，避免混乱）

| 层 | 谁负责 | 理由 |
|----|--------|------|
| **抓取/元数据/PDF 存储与标注** | **Zotero**（成熟 GUI，标注/高亮内置） | 这是 Zotero 的强项，重造轮子不值得 |
| **引用/笔记/检索/队列/统计** | **Anote**（纯文本契约） | 与知识库一体、可移植、可脚本化 |
| **电子书阅读（epub/mobi）** | **Foliate / Calibre**（专用阅读器） | 轻量阅读体验 |
| **统一入口** | **`anote read`**（自动路由） | 一个命令打开一切 |

一句话：**Zotero 管"读"（标注），Anote 管"学"（沉淀）**。

## 一、R1 · 阅读环境（手动阅读体验）

### 1.1 PDF 阅读（双模式）
| 模式 | 工具 | 场景 |
|------|------|------|
| 精读+标注 | **Zotero 内置阅读器**（高亮/批注/注释） | 核心论文 |
| 快速浏览 | **zathura**（vim 键位，已装） | 扫一眼/多文件对比 |

- `anote read <pdf>` → zathura（默认）
- `anote read --zotero <pdf>` → 导入 Zotero 并打开标注阅读
- 快捷键备忘写进 `docs/READING-PLAN.md` 附录

### 1.2 EPUB/MOBI 阅读
- 安装（一条命令，需要你确认 sudo）：
  ```bash
  sudo pacman -S foliate calibre      # foliate=epub阅读器 calibre=管理/转换
  ```
- `anote read xxx.epub` → foliate；`.mobi/.azw3` → calibre 或先 `ebook-convert` 转 epub
- foliate 支持书签、笔记导出（可导入 Anote 精读笔记）

### 1.3 阅读器路由表（`anote read` 增强）
| 后缀 | 阅读器 | 备注 |
|------|--------|------|
| .pdf | zathura（--zotero 用 Zotero） | 精读走 Zotero |
| .epub | foliate | 需安装 |
| .mobi/.azw3 | calibre / ebook-viewer | 需安装；可转 epub |
| .txt/.md | $editor | 直接编辑 |

### 1.4 阅读进度书签（跨会话续读）
- `anote read` 自动记录"上次打开的文件"；`anote docs progress <文件> [页数]` 记录进度
- 下次 `anote read` 提示"上次读到第 N 页"

## 二、R2 · 文档管理（极佳管理核心）

### 2.1 统一登记表（契约：docs/registry.md，MD 表格，人可读 + AI 可维护）
```
| 状态 | 类型 | 文件 | 标题 | 作者 | 年份 | 标签 | 笔记 | 进度 | 最后阅读 |
| 在读 | pdf | pdfs/xxx.pdf | ... | ... | 2024 | DL | src/papers/..tex | 45% | 2026-08-10 |
```
- 状态机：📥待读 → 📖在读 → ✅读完 → 🗄归档（与 queue.md 对齐）
- 字段：文件(相对路径)、标题、作者、年份、标签、笔记(精读笔记相对路径)、进度、最后阅读

### 2.2 `anote docs` 命令族
| 命令 | 功能 |
|------|------|
| `anote docs list [--status 在读] [--tag DL] [--sort 年份]` | 按状态/类型/标签过滤排序 |
| `anote docs add <文件> [--title --author --year]` | 注册新文档（自动提取元数据/去重 sha256） |
| `anote docs update <文件> --status ✅ --progress 100` | 更新状态/进度 |
| `anote docs progress <文件> <页数>` | 记录阅读进度 |
| `anote docs stats` | 统计：总数/在读/已读/未读堆积/本周阅读 |
| `anote import <目录>` | 批量扫描 PDF/epub → 注册+去重+提取 |

### 2.3 与既有系统联动
- **queue.md 同步**：registry 状态与队列状态一致（📖=在读）
- **check.py 新增检查**：pdfs/ 有文件但未登记；registry 指向的文件缺失
- **fetch_paper**：下载后自动 `docs add`
- **stats**：并入"文档数/在读数"

### 2.4 元数据富集（可选，经 Pi）
- `anote docs enrich --ai`：对缺作者/年份的条目，经 Pi 根据标题补全（你确认后写回）

## 三、R3 · 知识闭环（读→学）

### 3.1 标注 → 笔记
- Zotero 标注导出（右键 → 导出标注）→ `anote docs annotations <文件>` 导入 → 并入精读笔记（fetch_paper --tex-note 骨架）
- foliate 笔记导出 → 同路径

### 3.2 阅读即沉淀
- 读完（✅）自动提示：生成/更新精读笔记；周回顾统计本周读完数

### 3.3 文档内容进检索
- `anote index-pdf`（已有）批量提取 → 语义索引可选加入文档文本层（`anote index-docs`，分层：笔记层+文档层，检索可指定层）

## 四、里程碑（实施顺序，每步可独立用）

| 里程碑 | 内容 | 工作量 |
|--------|------|:---:|
| **M1 阅读环境** | ✅ foliate/calibre 已装；`anote read` 路由增强（zathura/foliate/calibre）+ 读即登记 | 半小时 |
| **M2 管理核心** | ✅ docs/registry.md 契约（11 列）+ `anote docs {list\|add\|update\|progress\|stats\|import}` + sha256 去重 | 1 天 |
| **M3 进度统计** | ✅ docs progress/stats、读即登记（📥→📖）、check 第 8 项、stats 并入 | 半天 |
| **M4 标注闭环** | Zotero 标注导入 → 精读笔记；阅读即沉淀 | 半天 |
| **M5 文档检索** | 文档文本语义层 `anote index-docs` | 半天 |

## 五、验收标准（每步完成判定）
- M1：`anote read` 三种格式各实测打开；进度跨会话续读
- M2：`anote docs list/add/update/stats` 全通；registry 契约文档化进 INTERFACES
- M3：check 全绿含新检查；周报含阅读统计
- M4：一条标注从 Zotero 到精读笔记的完整链路走通
- M5：`anote ask --semantic` 能命中文档层内容

## 附录 · 阅读器快捷键速查
| zathura | 含义 | foliate | 含义 |
|---------|------|---------|------|
| j/k | 下/上滚动 | PageUp/Down | 翻页 |
| / 搜索 n/N | 查找/下一个 | Ctrl+F | 查找 |
| o | 目录/跳页 | Ctrl+D | 书签 |
| a | 双页/单页切换 | Ctrl+E | 导出笔记 |
