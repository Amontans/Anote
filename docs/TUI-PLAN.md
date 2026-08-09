# Anote TUI 规划书（v0.7 设计文档）

> 状态：P0+P1+P2 已实现（v0.8.0-dev）。P3（迁移向导）待开发。目标：为 Anote 增加一个类 Pi Agent 的终端 TUI，让使用者**超快上手、忘记随时可查**，且**维护成本最低**。

## 一、设计原则（决定一切的三个铁律）

1. **薄壳原则**：TUI 只做"视图 + 编排"，**所有业务逻辑 100% 留在现有脚本**（manage.sh / scripts/*.py）。TUI 通过子进程调用同一套命令，绝不复制逻辑——这是"维护成本最低"的根本保证：改逻辑只改脚本，TUI 永远不用跟着改。
2. **配置单一源**：新增唯一配置文件 `~/.config/anote/config`（KEY=VALUE，bash/python 都能 3 行解析）。`data_dir` 等设置**从此不再硬编码**在脚本里——这是"数据位置可更改"的前提。
3. **数据契约不变**：TUI 读写数据一律遵守 `docs/INTERFACES.md` 的契约（META、queue.md、memory/*.md…），不新造格式。

## 二、技术选型

| 方案 | 依赖 | 优点 | 缺点 |
|------|------|------|------|
| **Textual（推荐）** | rich+textual（纯 Python，装进现有 .venv） | 现代组件、鼠标+键盘、主题、开发快、社区活跃 | 需 pip 安装；版本迭代 |
| stdlib curses | 零依赖 | 无外部依赖 | 开发慢、界面简陋、维护成本高 |
| fzf + bash | fzf | 极轻量 | 只是选择器，不是真正 TUI |
| dialog/whiptail | dialog | 简单 | 老式、丑 |

**推荐 Textual**：与语义检索共用 .venv；纯 Python 无编译依赖；组件化让帮助/面板/向导的实现成本最低。锁版本号防升级破坏。

## 三、架构

```
┌─────────────────────────────────────────┐
│  anote（Textual TUI，薄壳）               │
│  视图层: 页面/面板/表单/向导              │
│  编排层: 读 config → 调脚本 → 解析输出    │
├─────────────────────────────────────────┤
│  配置: ~/.config/anote/config            │  ← 新增（bash+python 双解析）
│  data_dir=~/Documents/Anote  editor=code │
├─────────────────────────────────────────┤
│  脚本层（不变，单一真相源）               │
│  manage.sh → scripts/*.py（--notes 改读  │
│  config 默认值）                          │
├─────────────────────────────────────────┤
│  数据层（不变，契约化）                   │
│  src/ memory/ books/ queue.md …          │
└─────────────────────────────────────────┘
```

## 四、配置设计（~/.config/anote/config）

```
data_dir=/home/Amontans/Documents/Anote   # 数据位置（可改，改时自动迁移）
editor=code                               # 外部编辑器
lang=zh                                   # UI 语言 zh/en
semantic_model=BAAI/bge-small-zh-v1.5     # 语义模型
onboarded=false                           # 新手引导完成标记
```
- 所有 python 脚本新增 `--notes` 默认值改为读此配置（新增共享模块 `scripts/anote_config.py`，~20 行）
- `manage.sh` 读取同一文件设置 `NOTES` 变量

## 五、TUI 页面地图

```
Home 仪表盘
├── 📝 笔记 Notes        —— 学科树浏览/预览/新建/编辑/检索
├── 📥 文献队列 Queue     —— 状态机表格/状态切换/检索入队/跳转精读
├── 🧠 记忆层 Memory      —— 日志/洞见/概念/问题 四页签
├── 📚 教科书 Books       —— 书/章节列表/新建/编译
├── 🔄 回顾 Review        —— 草稿查看/一键回顾
├── ⚙️ 设置 Settings      —— 数据位置(迁移向导)/编辑器/语言/语义模型
└── ❓ 帮助 Help          —— 新手引导/快捷键/命令手册/关于
```

### 各页要点
| 页面 | 内容 | 关键操作 |
|------|------|----------|
| **Home** | 数据目录、笔记数、队列计数(📥📖✅🗄)、语义索引状态、上次回顾、check 健康 | 一键 check；快速动作 |
| **Notes** | src/ 目录树 + 选中预览(META+正文头) | 新建(调 anote new)、编辑(调 $editor)、检索(调 ask.py，结果面板) |
| **Queue** | queue.md 表格渲染 | 状态切换、搜索入队(调 search.py --queue)、打开精读笔记 |
| **Memory** | 四文件页签，MD 渲染 | 追加条目、运行回顾(调 review.py)、查看草稿 |
| **Books** | 书/章节列表 | 新建书/章(调 anote book/chapter)、编译(调 book-build，输出面板) |
| **Review** | 最近回顾草稿 + 本周活动 | 一键"开始回顾"（生成草稿→提示确认） |
| **Settings** | 各设置表单 | **数据迁移向导**（见下） |
| **Help** | 命令手册全文 + 快捷键 | 随时 `?` 呼出 |

### 全局快捷键
```
? 帮助  / 命令面板(模糊搜索全部动作)  h 主页  n 笔记  q 队列
m 记忆  b 书  r 回顾  s 设置  esc 返回  F5 运行 check  Ctrl+D 退出
```

## 六、核心特性：数据迁移向导（重点设计）

**触发**：Settings → 数据位置 → 修改 → 启动向导。流程：

```
① 输入新路径（支持 ~ 展开，绝对路径校验）
   ↓
② 校验
   - 目标不存在 → 可创建 ✓
   - 目标存在且非空 → 拒绝（提示用空目录）
   - 检测是否跨文件系统（提示性能）
   ↓
③ 预览：将移动的条目清单 + 总大小（src/memory/books/projects/queue.md/
   roadmap.md/refs.bib/pdfs/latexmkrc/README.md/.git/.gitignore）
   排除：.semantic（重建）、.venv（重建）
   ↓
④ 确认 → 执行（写迁移日志 ~/.config/anote/migration.log）
   1) rsync -a 复制（排除 .semantic/.venv）
   2) 校验：文件计数一致（源 vs 目标）
   3) 更新 config data_dir
   4) 重建 .venv（python3 -m venv + pip install fastembed numpy）
   5) 重建语义索引（embed.py --full）
   6) 运行 check 验证（全绿才算成功）
   7) 询问是否删除旧目录
   ↓
⑤ 失败回滚：config 恢复旧值；旧目录未删 → 数据 100% 安全
```

**安全承诺**：任何一步失败都不动源数据；迁移完成前 config 不生效；全程有日志可查。

## 七、学习与提示系统（"超快上手 + 随时可查"）

| 机制 | 说明 |
|------|------|
| **新手引导 Onboarding** | 首次运行 3 步走：这是什么 → 怎么记笔记 → 怎么提问；完成后 config 记 `onboarded=true` |
| **上下文帮助 `?`** | 每页呼出：本页说明 + 本页相关命令 + 示例 |
| **状态栏提示** | 每页底部常驻显示该页快捷键 |
| **命令面板 `/`** | 模糊搜索所有动作（如输入"queue"即达队列操作） |
| **命令手册页** | 全部 `notes` 命令 + 示例（从 docs/WORKFLOW 提炼，**单一来源**） |
| **空状态引导** | 每页为空时显示"如何开始"（如队列空→教你怎么检索入队） |
| **AI 联动提示** | Help 页提示"细节可直接问 Pi——它已读 Anote 操作协议" |

**文档单点维护**：TUI 帮助文本由 `docs/` 生成/同步，不手写第二份——改文档即改帮助。

## 八、维护成本控制清单

- [ ] 薄壳：TUI 零业务逻辑，只调脚本/读契约数据
- [ ] 配置单文件双解析（bash/python 各 ~10 行）
- [ ] 帮助内容数据驱动（从 docs/ 生成）
- [ ] 迁移逻辑独立成 `scripts/migrate.py`（可单独测，TUI 只调它）
- [ ] 冒烟测试 = `./setup.sh && anote check` 全绿
- [ ] 版本锁：Textual 固定版本号

## 九、实施路线图（约 1 周单人）

| 阶段 | 内容 | 交付 |
|------|------|------|
| P0 | 配置化：anote_config.py + manage.sh/scripts 改读 config | ✅ 已完成（实测改 data_dir 后脚本跟随） |
| P1 | TUI 骨架：Textual 入口 + Home + Help + Settings 框架 | ✅ 已完成（冒烟测试 8 项通过；键位改 Ctrl 组合） |
| P2 | 数据页：Notes/Queue/Memory/Books/Review | ✅ 已完成（含写操作+集成测试） |
| P3 | 数据迁移向导（含 .git 一起搬 + 校验回滚）+ Onboarding | 待开发 |
| P4 | 命令面板、空状态、文档同步、测试 | v0.8.0 发布 |

## 十、待确认决策（实现前需要你拍板）

1. **TUI 框架**：Textual（推荐）还是零依赖 curses？
2. **范围裁剪**：八页全做，还是先做 Home + Notes + Settings(含迁移) + Help？
3. **编辑器联动**：`$editor` 默认 `code`（VS Code）还是 `vim`？
4. **迁移是否含 .git**：连同 git 历史一起搬（推荐），还是新数据目录重新 git init？
