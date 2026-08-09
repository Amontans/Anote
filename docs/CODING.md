# 代码规范（CODING）—— 现代化编程思想落地

> 本项目的代码约定：**任何新增/重构代码必须遵守**。目标：模块化、可测试、可扩展、低维护。
> 配套：`docs/INTERFACES.md`（数据契约）、`docs/HANDOFF.md`（交接）、`tests/`（单测）。

## 分层架构（模块化 + 单一职责）

```
表现层        CLI（scripts/*.py 薄适配器 + anote bash 编排）
               TUI（tui/screens + tui/widgets）
业务层        src/anote/ 包：core.py（配置/结果/日志）+ services.py（领域服务）
数据层        数据目录（纯文本契约，见 INTERFACES）
```

- **表现层禁止业务逻辑**：scripts/TUI 只做参数解析、展示、调服务；解析/计算一律进 `services.py`
- **scripts/*.py = 薄适配器**：3 行样板（sys.path → src）+ 调 anote 包 + 打印
- **TUI = 视图编排**：经 `tui/context.py`（依赖注入点）访问服务，不直接解析数据文件

## 已落地的现代实践

| 实践 | 落地位置 | 要求 |
|------|----------|------|
| **配置单点** | `anote/core.py::Config`（dataclass） | 新增配置键：加字段 + 文档；不散读文件 |
| **结果模式** | `anote/core.py::Result` | 命令/服务统一返回 Result，禁止裸 exit |
| **DRY** | `QueueService/NotesService/StatsService` | 同一格式只解析一次；新增解析先进 services |
| **类型提示** | 全包 | 新代码必须有类型注解；模型用 dataclass |
| **标准日志** | `setup_logging()` → `~/.config/anote/logs/` | 业务事件记日志，不用 print 调试 |
| **环境覆盖** | `ANOTE_DATA`（bash+python 都支持） | 测试/临时绝不改配置文件 |
| **测试门禁** | `tests/test_core.py` + `tui/test_smoke.py` + `tui/test_actions.py` | 改动后三套全绿才算完成 |
| **契约优先** | INTERFACES.md | 数据格式变更先改契约文档 |

## 文件职责约定

- `scripts/`：CLI 适配器（薄，≈50-150 行）；新命令先问"逻辑放 services 还是脚本"
- `src/anote/services.py`：领域服务（队列/笔记/统计）；新增领域（如 BookService）新建模块
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
