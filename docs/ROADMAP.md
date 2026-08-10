# Anote 功能路线图（ROADMAP）v3 —— 修正版

> 原则：每个版本先回答"价值 vs 维护成本"；**数据格式永远不破坏**。
> 执行顺序 = 下表流程（自上而下）；任何版本含 4 件套：功能 + 文档 + 测试 + CHANGELOG。

## 已实现
- v0.8 配置层/TUI 框架/数据页/迁移向导/引导/统计
- v0.9 检索增强（全文搜索/标签过滤/模板/每日笔记）
- v1.1 AI 经 Pi 问答/反链/回顾自动化/语义增量
- v1.2 插件机制/MCP Server/统一 CLI 守卫/模块契约声明/配置单点

## 执行流程（五阶段）

### 阶段一 · 闭环基础
| 版本 | 内容 | 状态 |
|------|------|:---:|
| **v1.3 Zotero 文献闭环** | Better BibTeX→refs.bib；`anote zotero`（status/bib/setup）；`anote bibcheck`；BibService（DRY）；stats/check 第7项/MCP anote_bib 集成 | ✅ anote 侧完成（GUI 步骤待用户：装插件+导出 refs.bib） |
| **v1.4 知识编译 + 数据质量** | `anote wiki`（--dry/--force/--branch，经 Pi 编译主题页）；`anote meta`（--ai 经 Pi 补全）；`core.ai_ask` AI provider 抽象（默认 pi） | ✅ 核心完成 |

### 阶段二 · 体验与质量
| 版本 | 内容 |
|------|------|
| **v1.5 多端协作 + 门禁** | Web 只读外壳（仅 127.0.0.1+口令）；Syncthing+KOReader 移动阅读；自动备份定时器；`anote export` 整库导出；**`anote test` 一键测试 + git hook 门禁** |
| **v1.6 体验图谱** | 知识图谱视图（META 标签/反链可视化）；主题系统；英文 UI；周报自动生成；**帮助分层 + `anote help <命令>`** |

### 阶段三 · 规模与安全
| 版本 | 内容 |
|------|------|
| **v1.7 性能规模** | 大库语义索引（分块/并行）；搜索分页；TUI 启动加速 |
| **v1.8 备份恢复 + 归档** | 加密冷备；异地副本；**恢复演练脚本**（dry-run 还原验证）；`anote archive` 年度归档/旧笔记冻结 |

### 阶段四 · 检索与输出
| 版本 | 内容 |
|------|------|
| **v1.9 检索质量** | BM25+向量混合检索；交叉重排；评测集（抽样问答看命中率） |
| **v1.10 写作输出** | 与 Pi academic-writing 融合；综述素材包（反链+主题页）；`anote paper`；投稿检查清单 |

### 阶段五 · 发布生态
| 版本 | 内容 |
|------|------|
| **v2.0 发布** | 开源发布（示例数据/CI）；`anote plugin new` 插件模板；MCP 工具增强（zotero/daily/migrate/backlinks）；`anote-pi-skill` 打包 |

## 持续优化（每版伴随）
- 错误路径审计（cli.run 已统一）
- 性能基准脚本（benchmark）
- 日志查看 `anote log`
- 数据安全演练（迁移回滚/冷备恢复）

## 铁律（任何版本不得违反）
- `src/` 笔记格式、META 契约、memory/ 结构 = 冻结层，永不破坏
- 新功能纯新增：派生物可重建、参数带默认值
- 每功能四件套：文档（INTERFACES/ROADMAP）+ 测试 + CHANGELOG + 注册命令

## 长期愿景
个人科研操作系统：本地优先 · 纯文本 · AI 编排（经 Pi）· 可插拔 → 开源发布 → 与 Pi 深度互操作（MCP）。
