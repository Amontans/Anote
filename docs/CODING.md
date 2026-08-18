# 代码规范（CODING）—— 现代化编程思想落地

> 本项目的代码约定：**任何新增/重构代码必须遵守**。目标：模块化、可测试、可扩展、低维护。
> 配套：`docs/INTERFACES.md`（数据契约）、`docs/HANDOFF.md`（交接）、`tests/`（单测）。

## 分层架构（模块化 + 单一职责）

```
表现层        CLI（scripts/*.py 薄适配器 + anote bash 编排）
               TUI（tui/screens + tui/widgets）
业务层        src/anote/ 包：core.py（配置/结果/日志/路径）+ services/（22 领域服务）
数据层        数据目录（纯文本契约，见 INTERFACES）
```

- **表现层禁止业务逻辑**：scripts/TUI 只做参数解析、展示、调服务；解析/计算一律进 `services/`
- **scripts/*.py = 薄适配器**：3 行样板（sys.path → src）+ 调 anote 包 + 打印
- **TUI = 视图编排**：经 `tui/context.py`（依赖注入点）访问服务，不直接解析数据文件

## 已落地的现代实践

| 实践 | 落地位置 | 要求 |
|------|----------|------|
| **配置单点** | `anote/core.py::Config`（dataclass，配置在 `<数据根>/.anote/config`） | 新增配置键：加字段 + 文档；不散读文件 |
| **结果模式** | `anote/core.py::Result` | 命令/服务统一返回 Result，禁止裸 exit |
| **DRY** | `QueueService/NotesService/StatsService` | 同一格式只解析一次；新增解析先进 services |
| **类型提示** | 全包 | 新代码必须有类型注解；模型用 dataclass |
| **标准日志** | `setup_logging()` → `<数据根>/.anote/logs/`；不可写自动降级 stderr | 业务事件记日志，不用 print 调试 |
| **环境覆盖** | `ANOTE_DATA`（bash+python 都支持） | 测试/临时绝不改配置文件 |
| **测试门禁** | `tests/test_core.py` + `tui/test_smoke.py` + `tui/test_actions.py` | 改动后三套全绿才算完成 |
| **契约优先** | INTERFACES.md | 数据格式变更先改契约文档 |

## 文件职责约定

- `scripts/`：CLI 适配器（薄，≈50-150 行）；新命令先问"逻辑放 services 还是脚本"
- `src/anote/services/`：领域服务包（一领域一模块）：queue/notes/stats/bib/health/wiki/graph/meta/review/semantic
- 新增领域 → `services/<领域>.py` + `__init__.py` 一行导出；脚本只留 参数解析+输出
- `src/anote/core.py`：横切关注点（配置/结果/日志/路径安全）
- `tui/screens/`：一屏一文件；数据访问仅经 `self.app.context`
- `templates/`：TEX 模板（占位符 `%%XXX%%`）
- `tests/`：与业务层一一对应的单测（unittest，临时目录隔离）

## 新功能检查清单（扩展时逐项过）

1. [ ] 业务逻辑在 services（不是脚本/TUI 内联）
2. [ ] 配置经 Config 单点；格式经对应 Service
3. [ ] 返回 Result；类型注解完整
4. [ ] 注册：`anote` 命令 + `scripts/` 适配器 + INTERFACES 表
5. [ ] 单测（services 逻辑）+ 冒烟/动作回归全绿
6. [ ] 文档：README/CHANGELOG/HANDOFF/ROADMAP 相应更新
7. [ ] `anote check` 全绿

## 演进方向（可选，不强制）

- `pyproject.toml` + `pip install -e`（src-layout 已就绪，随时可加 console 脚本）
- mypy 类型检查（包内类型已就绪）
- 更多服务拆分（BookService/ReviewService/MemoryService）
- 插件机制（v1.2：scripts/ 注册表）


## 简洁化检查清单（代码评审用）
- [ ] 脚本 ≤150 行且无业务逻辑（解析/计算在 services）
- [ ] 无重复解析（同一格式只一个 Service 拥有）
- [ ] 无死代码/未用 import；类型注解完整
- [ ] 数据访问经 Service 或 context，不散落
- [ ] 错误走 Result + cli.run（不裸 print traceback）

---

# 开发流程（原 PROCESS）
> 本文件定义"一个版本如何从想法到发布"。配合 ROADMAP（规划）、CODING（实现规范）、HANDOFF（交接）。

## 版本生命周期（六步，每版走完）

```
① 规划    ROADMAP 立项：定版本范围 + DoD 清单（先写验收标准再动手）
② 实现    按 CODING.md：模块化分层、契约声明、薄适配器、anote 注册
③ 验证    anote test 门禁：单测 + TUI 双测试 + check 全绿
④ 文档    四件套：INTERFACES + CHANGELOG + HANDOFF + ROADMAP（功能/接口/状态同步）
⑤ 验收    用户过一遍新功能（功能演示 → 反馈 → 记录进 HANDOFF）
⑥ 发布    anote release <major|minor|patch>：门禁复查 + VERSION 递增 + git tag
```

## 变更纪律

| 场景 | 必须做 |
|------|--------|
| 新增功能 | DoD 四件套 + 注册命令 + 单测 |
| 改数据格式 | 先改 INTERFACES（契约先行）+ 兼容/迁移 |
| 冻结层（src/META/memory） | **永不破坏性变更**；新字段必须可选 |
| 修 bug | 补回归测试 + CHANGELOG 修复条目 |
| 依赖变更 | 更新 setup.sh + HANDOFF 环境清单 |

## 发布门禁（anote release 自动执行）

```bash
anote release minor
# 1) anote test（不过则中止） 2) VERSION 递增 3) git commit+tag vX.Y.Z
```

## 决策记录纪律
- 重大决策（架构/格式/工具选型）→ 写进 HANDOFF「决策记录」+ Engram（mem_save）
- 每个决策带"为什么/哪里/踩坑"

## 小步迭代原则
- 每版独立可用、可随时停；版本自治
- 用户验收节点 = 版本结束（如同日常对话）
- 风险登记见 ROADMAP §3；高优先项（P0）可跳过中间版本提前做

---

# 扩展与升级（原 DEVELOPMENT）
> 合并自原 EXTENDING + UPGRADING。**不读全部代码即可安全扩展或升级。**

## 一、扩展检查清单（新增功能）

| 步骤 | 要求 |
|------|------|
| 1. 位置 | `scripts/<名>.py`，单一职责，100-300 行 |
| 2. CLI 契约 | argparse 或薄解析；数据根由 `ANOTE_DATA`/默认目录决定；stdout=结果 stderr=错误；退出码 0/1 |
| 3. 注册 | `anote` 加 case + usage 行 + 模糊建议词表（`manage.sh` 仅兼容包装） |
| 4. 自检 | 涉及结构一致性时在 `check.py` 加 `check_N` |
| 5. 文档 | 更新 `docs/INTERFACES.md` 表格 + `CHANGELOG.md` |
| 6. 验证 | `anote check --strict` 全绿 + `anote test` + 功能实测 |

新增命令模板（anote）：
```bash
  mycmd)
    python3 "$SKILL/my_script.py" "$@" ;;
```

## 二、组件替换路径（升级就绪）

| 替换 | 做法 | 数据影响 |
|------|------|:---:|
| 换嵌入模型 | `.anote/config` 改 `semantic_model` 或 `embed.py` 默认值 → `rm -rf .semantic && anote index-semantic --full` | 无 |
| 换向量库（ChromaDB 等） | 只改 `embed.py`（写）与 `ask.py::semantic_search`（读），CLI 接口不变 | 无 |
| 加 Web 外壳 | 新目录，只读 `src/` + `.semantic/`，写经 `anote commit` | 无 |
| 加知识编译层（wiki） | 新增 `wiki.py`，读 `src/` 写 `memory/` | 无 |

## 三、接口变更纪律

- 冻结格式（**永不破坏**）：`src/` 笔记+META、`memory/` 结构、`queue.md` 列结构
- 可重建派生物（随便改）：`.semantic/`、`00-index.tex`、`reviews/`、`.anote/logs/`、`.anote/backups/`
- 新增参数必带默认值（=旧行为）；删功能先弃用一版；任何变更更新 CHANGELOG

## 四、版本历史

| 版本 | 内容 |
|------|------|
| 0.1-0.3 | 结构 → 记忆闭环 → 队列/项目/自检 |
| 0.4 | XDG 迁移；ask.py 关键词检索 |
| 0.5 | 语义检索(B)；教科书层；文档体系；脚本归项目 |
| **0.6** | **setup.sh 自举；AI 操作协议；精简（删 notes.py 旧流程，合并文档）** |

## 五、升级步骤（通用）

```bash
cd <项目目录>
git pull                        # 有远程时
./setup.sh                      # 自举（骨架/依赖/venv/索引/自检）
anote check --strict            # 全绿即完成
```
任何时刻 `src/` 完好 ⇒ 系统可 100% 重建。
