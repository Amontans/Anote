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
| **v1.6 体验图谱** | `anote graph [--mermaid]` 图谱；主题系统（Settings 选择）；`anote report` 周报；`anote help <命令>` 分层 | ✅ 核心完成（i18n 转 P2） |

### 阶段三 · 规模与安全
| 版本 | 内容 |
|------|------|
| **v1.7 性能规模** | 大库语义索引分块/并行嵌入；`anote ask` 结果分页；TUI 懒加载加速；基准脚本 benchmark.py |
| **v1.8 备份恢复 + 归档（P0）** | `anote backup-create [--encrypt]`（tar.gz+sha256/openssl 加密）；`anote restore [--dry-run/--force]` 校验+演练+还原；`anote archive <年份>` 归档冻结（自动排除检索）；每日定时器周日自动加密冷备 | ✅ 完成 |

### 阶段四 · 检索与输出
| 版本 | 内容 |
|------|------|
| **v1.9 检索质量** | `services/retrieval.py`：BM25 词法+向量混合（可调权重）+轻量重排；`anote ask --semantic` 升级混合、`--bm25` 纯词法；`anote eval` 评测（自命中+人工查询集） | ✅ 完成 |
| **v1.10 写作输出** | `anote paper <主题> [--type 论文\|综述\|开题]`（素材聚合 BM25+引用+wiki → 经 Pi 生成骨架 → projects/<主题>/{paper.tex,materials.md}）；`anote checklist` 投稿检查清单 | ✅ 完成 |

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

## 流程科学性（方法论自审）

### 1. 定义完成标准（DoD，每版验收清单）
- [ ] 功能全部可用（命令/TUI 实测）
- [ ] `anote test` 门禁通过（单测 + TUI 双测试 + check 全绿）
- [ ] 文档四件套更新（INTERFACES/CHANGELOG/HANDOFF/本 ROADMAP）
- [ ] 无冻结层破坏（src 格式/META/记忆层结构不变）

### 2. 版本依赖图（执行顺序的科学依据）
```
v1.3 Zotero ──► v1.4 知识编译/META（供数给）──► v1.6 图谱
v0.9 语义索引 ──► v1.9 检索质量（在其上增强）
v1.4 wiki 层 ──► v1.10 写作输出（综述素材来源）
v1.2 MCP ──► v2.0 生态（基础已稳）
```
依赖解锁原则：先做"被依赖项"，再做"依赖项"——当前顺序即依赖拓扑序。

### 3. 风险登记（含缓解）
| 风险 | 概率 | 影响 | 缓解 |
|------|:---:|:---:|------|
| 用户 GUI 步骤阻塞（Zotero/BBT） | 高 | 中 | 已提供替代路径（BIBINPUTS/沙盒验证）；anote 侧全部可先行 |
| AI 经 Pi 的延迟/成本 | 中 | 中 | core.ai_ask 抽象，未来可换 provider；本地检索兜底 |
| 大库性能（万级笔记） | 中 | 中 | v1.7 预留；语义索引可重建 |
| 单一数据目录损坏 | 低 | 高 | v1.8 备份恢复（加密冷备+演练）；git 兜底 |
| 功能膨胀导致维护负担 | 高 | 中 | 薄壳原则+CODING 规范+测试门禁；每功能过 DoD 才合入 |

### 4. 优先级标注（P0=必做 / P1=重要 / P2=可选）
- P0：v1.8 备份恢复（数据安全命脉）→ v1.9 检索质量 → v1.10 写作输出
- P1：v1.5 门禁/备份定时器 → v1.6 图谱/帮助 → v1.7 性能
- P2：Web 外壳细化、移动端指引、主题/i18n

### 5. 验证节奏（小步迭代，每版可独立使用）
每版结束 = 一次用户验收（如同本次）：功能演示 → 用户反馈 → 记录进 HANDOFF → 下版。
原则：任何版本可中途停止，系统保持可用（版本自治）。

## 后续规划（v2.x+，随用随定）
| 版本 | 方向 |
|------|------|
| **v2.0 发布生态** | 开源发布（示例/CI）；`anote plugin new`；MCP 增强；anote-pi-skill 打包 |
| **v2.1 AI 深度** | 反链图谱可视化（graph 数据已有）；TUI AI 面板会话记忆；自动标注/笔记质量建议（经 Pi） |
| **v2.2 协作分享** | Web 外壳增强（图谱/周报页）；`anote export --html` 静态站；只读分享链接（局域网） |
| **v2.3 学习分析** | 检索日志（失败查询收集→补 eval 集）；学习投入统计（笔记/阅读趋势周报） |
| **v2.4 通用化** | 插件市场雏形；i18n 完整；主题市场 |
| **长期愿景** | 个人科研操作系统：本地优先·纯文本·AI 编排（经 Pi）·可插拔 → 开源发布 → 与 Pi 深度互操作（MCP） |
