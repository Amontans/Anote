# 开发流程（PROCESS）—— Anote 版本生命周期

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
