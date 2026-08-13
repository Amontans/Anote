# 项目审计（AUDIT）—— 轻量 + 任意输入输出兼容

> 依据升级后大模型重新审查。两把尺子：①轻量 ②任意形式输入输出。

## 一、轻量审计

### 依赖分层（现状）
| 层 | 依赖 | 体积 | 加载时机 |
|----|------|------|----------|
| **核心**（scripts + services） | 纯 Python stdlib + 系统工具 | ≈0 额外 | 总是（极轻） |
| 系统工具 | pandoc/latexmk/pdftotext/rg/git/node/openssl/tar | 已装 | 按需 |
| 语义检索 | fastembed+onnxruntime+numpy+tokenizers | ~130MB | **lazy import**（不用不加载） |
| TUI | textual+rich+pygments | ~60MB | 仅 anote tui |
| MCP | fastmcp+mcp+cryptography | ~40MB | 仅 anote mcp |

**结论**：核心零第三方依赖；重型功能（语义/TUI/MCP）全部懒加载，内存按需占用。

### 轻量化改进
1. **依赖分层安装**：`setup.sh --minimal`（核心，零 pip）vs `--full`（含 fastembed/textual/fastmcp）
2. 保持 lazy import 模式（semantic/tui/mcp 都在调用时才 import）
3. 语义检索已有 **BM25 兜底**（零依赖），可脱离 fastembed 运行

## 二、任意输入输出审计

### 格式兼容矩阵（现有 + pandoc 补强后）
| 方向 | 格式 |
|------|------|
| **输入** | TEX / MD / PDF(pdftotext) / epub(zipfile) / BibTeX / CSL JSON / Zotero JSON + **pandoc**: docx/pptx/odt/ipynb/org/rst/html/csv/mediawiki 等 40+ |
| **输出** | TEX / MD / PDF(latexmk) / JSON / HTML(web) / tar.gz(备份导出) + **pandoc**: docx/epub/beamer/pptx 等 40+ |
| **协议** | CLI / MCP(server) / HTTP(web) / JSON-RPC + 规划 LSP / 文件监听 |
| **插件** | anote plugins/（python 薄适配器）+ **portkit IR**（任意↔任意，已验证） |

### 改进项（按价值）
1. ✅ **`anote convert`**（pandoc 包装）——立即获得 40+ 格式双向互通
2. MCP client（接入外部 MCP server 的能力）
3. LSP 接入（texlab，编辑器级补全/检查）
4. 文件监听（inotify，自动索引变更）

## 三、结论
- **轻量**：核心零依赖；重型功能分层懒加载 ✅
- **任意 I/O**：pandoc(40+ 格式) + portkit(任意插件↔任意) + MCP(任意 AI 工具) 三枢纽 ✅
- 三条铁律不破：薄壳 / 纯文本契约 / 可移植

## 四、待办
- [ ] setup.sh 分层安装（--minimal/--full）
- [ ] `anote convert` 补 epub/mobi 双向
- [ ] MCP client + LSP（依赖确认后）
