# Anote 用户手册（USER-GUIDE）

> 面向用户，简明全面。5 分钟上手，忘了随时回来看。命令详情：`anote help <命令>`。

## 一、5 分钟上手

```bash
./setup.sh                     # 首次安装（数据骨架/venv/索引/命令/定时器）
anote                          # 打开菜单（不知道用什么时）
anote ai "帮我找关于X的论文"     # 说人话，AI 自动执行
anote new 数学/代数 "标题"      # 记笔记
anote ask --semantic "问题"     # 问知识库
```

## 二、常用命令速查（按场景分组）

### 📝 记笔记 / 写作
| 想做什么 | 命令 |
|----------|------|
| 新建笔记 | `anote new 学科/分支 "标题"` |
| 写论文骨架 | `anote paper "主题" [--type 论文\|综述\|开题]` |
| 写书 | `anote book "书名"` → `anote chapter` → `anote book-build` |
| 语法检查 | `anote lint 笔记.tex` |
| 投稿前 | `anote checklist` |

### 🔍 提问 / 检索
| 想做什么 | 命令 |
|----------|------|
| 问知识库 | `anote ask "关键词"`（grep 快） |
| 模糊问 | `anote ask --semantic "自然语言"`（混合检索） |
| 只查文档层 | `anote ask --semantic --layer docs "..."` |
| 问 AI（带引用） | `anote ask-pi "问题"` |
| 检索质量评测 | `anote eval` |

### 📚 文献 / 文档
| 想做什么 | 命令 |
|----------|------|
| 读文档 | `anote read pdfs/xxx.pdf` |
| 读论文（一条龙） | `anote 读论文 2402.00001`（= fetch+提取+笔记+登记） |
| 文档管理 | `anote docs list / stats / add / progress` |
| 导入标注 | `anote docs annotations 标注.md` |
| 转换格式 | `anote convert a.md --out a.docx` |

### 🛠 维护
| 想做什么 | 命令 |
|----------|------|
| 自检 | `anote check`（7+ 项） |
| 保存 | `anote commit "说明"` |
| 备份 | `anote backup`（或 `anote backup-create --encrypt`） |
| 周回顾 | `anote review` |
| 统计 | `anote stats` |
| 打开 TUI | `anote tui` |

## 三、典型工作流

**① 读一篇论文**：
```
anote 读论文 2402.00001     → 下载+提取+生成精读笔记+登记
（精读后）anote docs progress pdfs/2402.00001.pdf 50%
（沉淀）anote wiki --dry  → 确认 → 生成主题页
```

**② 从读到写**：
```
anote ask --semantic "主题"  → 检索相关笔记
anote paper "主题" --type 综述 → 生成骨架（素材自动聚合）
anote bibcheck               → 校验引用
latexmk 编译 → anote checklist → 投稿
```

**③ 每周维护**：
```
anote check（自检）→ anote review（回顾草稿，AI 提炼你确认）
→ anote commit "本周" → anote backup
```

## 四、提示辅助（不用记命令的原因）

| 辅助 | 触发 |
|------|------|
| 友好菜单 | `anote`（无参数） |
| 模糊纠错 | 打错命令自动建议（`anote chekc` → "是不是想说 check?"） |
| 命令示例 | `anote help <命令>` |
| 下一步提示 | 操作后自动给 💡 提示 |
| 说人话 | `anote ai "你想做什么"` |

## 五、故障速查

| 现象 | 解决 |
|------|------|
| 语义检索提示"未建索引" | `anote index-semantic` |
| check 报"缺 META" | 笔记前加 `% ==META== 学科: X | 日期: YYYY-MM-DD` |
| check 报"未登记" | `anote index` 或 `anote docs import` |
| 误删文件 | `git log --oneline` → `git checkout <commit> -- <文件>` |
| 语义缓存坏了 | `rm -rf .semantic && anote index-semantic` |
| 系统整体损坏 | `./setup.sh` 自举重建（数据无损） |
| 忘了怎么用 | `anote`（菜单）或 `anote help` 或直接问 Pi |

## 六、数据在哪（可移植）

- 代码：项目目录（MIT；**不含任何用户数据**，可直接上传 GitHub）
- 你的数据：数据根（默认 `~/Documents/Anote/`，`ANOTE_DATA` 可覆盖）
  - 笔记/文献/书/项目/队列在数据根下
  - **配置、日志、外部 MCP 注册、默认备份**都在数据根的 `.anote/` 内
- 换电脑：整目录拷贝数据根 + 项目 → `./setup.sh` → `anote check` 全绿
- 修改数据根位置：`anote migrate --to <新路径>`，或 TUI 设置页直接修改“数据目录”后保存（自动迁移）；`~/.config/anote/config` 只保留 `data_dir=` 定位指针
