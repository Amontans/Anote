# Anote —— 个人科研知识库操作系统

> 纯 TEX/MD 资产 + git 版本化 + AI（经 Pi）编排。**说人话即可用：`anote ai "帮我…"`**。

**版本**: 1.15.0 · **协议**: MIT · **依赖**: 核心零第三方（重型功能按需）

## 🚀 快速开始

```bash
./setup.sh                     # 首次/换机：初始化数据目录 + venv + 索引 + 命令 + 定时器
# 或先装 Python 包: pip install -e ".[full]"（bash 入口仍用 ./setup.sh 安装）
anote                          # 打开菜单（不知道用什么时）
anote ai "帮我找关于X的论文"     # 说人话，AI 自动执行
anote new 数学/代数 "标题"      # 记笔记
anote ask --semantic "问题"     # 问知识库
anote read pdfs/xxx.pdf         # 读文档
anote commit "说明"             # 保存（自动索引+自检）
```

## 📚 文档导航（按需读，不用全看）

| 我是谁 | 读什么 | 内容 |
|--------|--------|------|
| **用户**（日常使用） | `docs/USER-GUIDE.md` | 5 分钟上手 + 命令速查 + 工作流 + 故障速查 |
| **AI/维护者**（接手项目） | `docs/HANDOFF.md` | 交接总纲：全部路径/命令/契约/踩坑/下一步 |
| 开发/扩展 | `docs/CODING.md` | 代码规范 + 开发流程 + 扩展升级 |
| 排查格式 | `docs/INTERFACES.md` | 数据格式/命令接口契约 |
| 了解架构 | `docs/ARCHITECTURE.md` | 分层与数据流 |
| 看规划 | `docs/ROADMAP.md` | 路线图（已做/待做） |
| 历史决策 | `docs/archive/` | 已归档的分析/规划文档 |

> 记不住命令？① `anote` 看菜单 ② 打错自动纠错 ③ `anote help <命令>` 带示例 ④ `anote ai` 说人话。

## 📁 目录结构

```
<项目目录>/               # 代码+文档（MIT；无任何用户数据，可直接上传 GitHub）
├── anote  setup.sh       # 统一入口 / 一键自举（自动推导项目路径）
├── scripts/              # 42 个 Python + 4 个 shell 薄适配器（CLI）
├── src/anote/            # 业务逻辑包（core + services 22 领域）
├── tui/                  # 终端界面（10 屏）
├── templates/            # 笔记/精读/教科书/项目模板
├── config/               # systemd 模板（@@PROJECT@@ 占位）与 git hooks 模板
├── docs/                 # 文档（见上导航）
└── tests/                # 测试（门禁）

<数据根>（默认 ~/Documents/Anote；ANOTE_DATA 可覆盖）＝唯一用户数据位置
├── src/                  # 笔记（TEX，唯一真相源）
├── memory/               # 记忆层（日志/洞见/概念/问题/回顾/周报）
├── books/ projects/      # 教科书 / 研究项目
├── docs/registry.md      # 文档登记表
├── queue.md roadmap.md refs.bib
├── pdfs/ ebooks/         # 文档库
└── .anote/               # ★ 配置/config、日志/logs、MCP注册、迁移日志、backups/
```

## ✨ 核心能力

- **三级管线**：笔记(src) → 知识编译(wiki) → 教科书(books)
- **混合检索**：BM25 + 向量语义 + 分层（笔记/文档）
- **三枢纽互通**：pandoc(40+格式) / portkit(任意插件) / MCP(任意 AI 工具)
- **轻量**：核心零依赖；重型功能懒加载；`setup.sh --minimal`
- **数据安全**：git + 每日备份 + 周日加密冷备（默认 `.anote/backups/`）+ 迁移向导(含.git)
- **可移植**：**所有用户数据（配置/日志/API注册/文档）都在数据根内**；项目仓库无用户数据，可直接开源上传；数据目录拷走即无缝衔接
