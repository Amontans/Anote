# 插件转接器框架（ADAPTERS）—— 把外部插件纳入 Anote 生态

> 需求：把 Zotero / Obsidian 等软件的插件**当作 Anote 的插件使用，功能 100% 保留**。
> 途径：①协议级直接接入 ②宿主式转接器（规范输入输出）。

## 〇、技术真相（决定架构的唯一事实）

**插件 = 代码 + 宿主运行时 + 私有 API**。Zotero 插件必须跑在 Zotero 里（依赖 `Zotero.*` 内部对象），Obsidian 插件必须跑在 Obsidian 里（依赖 `app.vault` 等）。
**移植 = 重写宿主**（≈ 重写 Zotero/Obsidian），违背一切原则。

因此正确架构只有两条路，且互补：

```
路径 A（协议直连）：插件若遵循标准协议 → Anote 直接把它当插件用（真·直接接入）
路径 B（宿主转接）：插件留在它宿主里跑（功能 100% 保留），
                   Anote 通过"转接器 Adapter"规范输入输出并连接
```

## 一、路径 A：协议级直接接入（无需宿主）

插件只要输出/遵循**标准协议**，Anote 原生就能调用：

| 协议 | 能接什么"插件" | 例子 | 状态 |
|------|----------------|------|:---:|
| **MCP** | 任何 MCP server（AI/检索/数据工具） | 外部 MCP server 作为 Anote 工具 | 我们是 server，client 待做 |
| **LSP** | 语言服务（LaTeX/代码补全/检查） | texlab（LaTeX LSP）、clangd | 可接 |
| **CSL/BibTeX** | 引文样式与文献工具 | 任何 .csl 样式、bib 工具链 | ✅ 已兼容 |
| **pandoc filters** | pandoc 过滤器（文档转换增强） | 学术过滤、公式渲染 | 可接 |
| **JSON-RPC/HTTP** | 带标准 API 的服务 | Zotero 本地 API、BBT HTTP 端口 | 部分已用 |

**规则**：符合标准的"插件"→ `anote plugins add <mcp|lsp|...>` 直接注册，无转接成本。

## 二、路径 B：宿主式转接器（功能 100% 保留）

**核心模型**：外部软件 = Anote 的"插件宿主"；插件在宿主内照常运行（功能不减），Anote 通过 **Adapter** 双向连接。

### B.1 统一 Adapter 框架（Anote 侧，规范输入输出）

```
┌─ Anote 核心（services/，契约冻结）─────────────────┐
│  adapters/ 注册表（config: adapters.json）         │
│   接口: detect() → 宿主是否可用                    │
│         pull()  → 宿主产出 → 导入 Anote（标准化）   │
│         push()  → Anote 数据 → 宿主（标准化）      │
│         call(cmd) → 远程调用宿主功能               │
│  services/adapters/{zotero,obsidian,vscode,mcp}.py│
└───────────────────────────────────────────────────┘
         │ pull/push（标准格式：文件/HTTP/CLI）
┌─ 宿主（插件照常运行，功能 100% 保留）───────────────┐
│  Zotero（+ 全部 Zotero 插件，如 Better BibTeX）     │
│  Obsidian（+ 全部 Obsidian 插件，如 Dataview）      │
│  VS Code（+ 全部扩展，如 LaTeX Workshop）           │
└───────────────────────────────────────────────────┘
```

### B.2 各宿主 Adapter 设计

| 宿主 | 连接通道 | pull（宿主→Anote） | push（Anote→宿主） | 插件功能保留 |
|------|----------|--------------------|--------------------|:---:|
| **Zotero** | BBT HTTP API(:23119) + 文件导入 | 标注导出→精读笔记；元数据→registry | 检索结果→写入 Zotero 收藏夹；refs.bib 同步 | ✅ 全部 Zotero 插件照常 |
| **Obsidian** | memory/ 即 vault（文件层互通）+ 桥插件(可选) | vault 变更→anote 导入；Dataview 生成的仪表盘→导出 | anote 写入 memory/ → Obsidian 自动显示 | ✅ 全部 Obsidian 插件照常 |
| **VS Code** | Anote 扩展(转接器) + CLI | 编辑器状态→anote | 命令面板→anote 命令 | ✅ 全部扩展照常 |
| **MCP** | 标准协议 | 其他 MCP server 的工具→anote 工具 | anote→外部 | ✅ 协议级 |

### B.3 命令（`anote adapters`）
```
anote adapters list                 # 检测各宿主/插件可用性
anote adapters connect zotero       # 建立连接（检测 API/路径）
anote adapters pull zotero          # 导入宿主产出（标注/元数据）
anote adapters push obsidian        # 推送 Anote 数据到宿主
anote adapters call zotero add-item # 远程调用宿主能力
```

## 三、为什么这是"功能 100% 保留"的正解

- 插件**从未离开它们的宿主** → 逻辑/UI/数据完整保留（不是移植，不降级）
- Anote 只做"进口/出口/遥控" → 薄壳原则不破，维护成本可控
- 将来任何宿主更新插件，Anote 无感（adapter 只依赖标准通道）

## 四、实施计划（按性价比排序）

| 优先 | 项 | 内容 | 工作量 |
|:---:|----|------|:---:|
| P0 | **Adapter-Zotero（pull）** | 标注导入（M4 顺带）+ 元数据→registry | 1 天 |
| P0 | **MCP client 接入** | 让外部 MCP server 成为 Anote 工具（`anote plugins add mcp://...`） | 1 天 |
| P1 | **Adapter-Obsidian** | memory/ vault 互通文档 + 桥插件（可选）+ push | 1-2 天 |
| P1 | **Adapter-VSCode** | Anote 扩展（侧边栏） | 几天 |
| P2 | **LSP 接入** | texlab（LaTeX 检查/补全）进 TUI/编辑器 | 1 天 |
| P2 | Adapter-Zotero（push） | 检索结果写入 Zotero 收藏夹 | 半天 |

## 五、契约（INTERFACES 增补）
- `services/adapters/*.py`：每个宿主一个模块，实现统一接口（detect/pull/push/call），输入输出全部标准化
- `adapters.json`：注册表（宿主、通道、状态）
- 任何新宿主 = 新增一个 adapter 模块 + 注册，不动核心

## 六、待你确认
1. 先做 **P0：Adapter-Zotero pull + MCP client**（1-2 天见效）？
2. 还是先 **Adapter-Obsidian**（把 memory/ 变成可互通的 vault，Obsidian 插件立刻可用）？
3. Adapter 框架接口设计（detect/pull/push/call）是否认可？
