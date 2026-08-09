# Anote 功能路线图（ROADMAP）

> 原则：每个版本先回答"价值 vs 维护成本"；**数据格式永远不破坏**（冻结层见 INTERFACES）。
> 参考成熟软件：Pi（对话/技能/MCP）、Obsidian（双链/图谱/模板/插件）、Joplin/Logseq（标签/搜索/日记）。

## 已实现（v0.8-dev）
- 纯 TEX 资产 + git 版本化；三级管线（src → memory/books）
- 语义检索（bge-small-zh 向量缓存）；关键词检索（rg 片段）
- 教科书工作流（ctexbook）；待读队列；记忆层；自检雷达；周回顾
- **TUI**（8 屏 + 命令面板 + 新手引导 + 数据迁移向导含 .git 随迁）
- **统一入口 `anote <command>`**；`anote stats` 文件统计

## 规划版本

### v0.9「检索增强」（✅ 已完成 2026-08-09）
| 功能 | 参考 | 价值 | 成本 |
|------|------|:---:|:---:|
| META 标签浏览/过滤面板（按 学科/标签 筛选笔记） | Obsidian 标签 | ✅ | 低 |
| TUI 全文搜索页（rg 集成，结果+行号+跳转） | Obsidian 搜索/Joplin | ✅ | 中 |
| 笔记模板系统（`templates/` 多模板选择） | Obsidian 模板 | ✅ | 低 |
| 每日笔记（自动生成日期页 + 当日队列/回顾入口） | Obsidian daily notes | ✅ | 低 |

### v1.0「稳定版」
- 迁移向导 + Onboarding 打磨（已具备，补全异常路径与文档）
- 测试矩阵完备（setup.sh + check + smoke/actions 全绿为发布门禁）
- 发布流程：CHANGELOG / VERSION / git tag；数据仓库一键 `anote backup`

### v1.1「AI 深度集成」（对标 Pi 的对话式体验）
| 功能 | 参考 | 价值 | 成本 |
|------|------|:---:|:---:|
| **TUI 内 AI 问答面板**（**经 Pi 代理**：Ctrl+A，Pi 按 Anote 协议自动检索知识库作答） | Pi 对话 | ✅ | 中 |
| **反链/引用视图**（概念 ← 被哪些笔记/书引用） | Obsidian 反链 | 高 | 中 |
| 回顾自动化增强（AI 草拟→你确认→一键写入 memory/） | Pi 技能 | 高 | 低 |
| 语义索引自动增量（pre-commit 触发 embed 增量） | — | 中 | 低 |

### v1.2「插件与生态」（对标 Pi 技能/Obsidian 插件）
| 功能 | 参考 | 价值 | 成本 |
|------|------|:---:|:---:|
| **插件机制**：`scripts/` 插件注册表 + `anote plugin` 命令（第三方脚本一键注册） | Pi skills / Obsidian 插件 | 高 | 中 |
| **MCP Server**：对外暴露 anote 能力（search/ask/queue/notes）给其他 AI 工具 | MCP 生态 | 高 | 中 |
| 自定义快捷键/别名 | Obsidian 热键 | 中 | 低 |

### v1.3「多端与协作」
| 功能 | 参考 | 价值 | 成本 |
|------|------|:---:|:---:|
| Web 只读外壳（局域网浏览器访问 src/memory，搜索） | Obsidian Publish | 中 | 中 |
| 移动端阅读（配合 Syncthing + KOReader，PDF 已可） | — | 中 | 低 |
| 自动提交定时器（每日 git commit + 每周 push） | — | 中 | 低 |

### v1.4「体验」
| 功能 | 参考 | 价值 | 成本 |
|------|------|:---:|:---:|
| 主题系统（Textual 主题切换） | Obsidian 主题 | 中 | 低 |
| 完整英文 UI（i18n） | — | 低 | 低 |
| **知识图谱视图**（META 标签/引用关系可视化） | Obsidian graph | 中 | 高 |
| 周报自动生成（每周回顾 → markdown 周报） | daily/weekly 工具 | 中 | 低 |

## 优先级排序（建议执行顺序）

1. **v1.1 的 AI 问答面板**（价值最高，与你的 DeepSeek 使用闭环）
2. **v0.9 标签 + 全文搜索**（检索体验立竿见影）
3. **v1.2 插件机制 + MCP**（让外部 AI 工具复用 anote）
4. 其余按需

## 铁律（任何版本不得违反）
- `src/` 笔记格式、META 契约、memory/ 结构 = 冻结层，永不破坏
- 新功能默认"纯新增"：派生物可重建、参数带默认值
- 每个功能必须配套：文档（INTERFACES/ROADMAP 更新）+ 测试 + CHANGELOG
