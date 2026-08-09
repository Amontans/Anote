# 开发与升级指南（DEVELOPMENT）

> 合并自原 EXTENDING + UPGRADING。**不读全部代码即可安全扩展或升级。**

## 一、扩展检查清单（新增功能）

| 步骤 | 要求 |
|------|------|
| 1. 位置 | `scripts/<名>.py`，单一职责，100-300 行 |
| 2. CLI 契约 | argparse；`--notes` 默认 `~/Documents/Anote`；stdout=结果 stderr=错误；退出码 0/1 |
| 3. 注册 | `manage.sh` 加 case + usage 行 |
| 4. 自检 | 涉及结构一致性时在 `check.py` 加 `check_N` |
| 5. 文档 | 更新 `docs/INTERFACES.md` 表格 + `CHANGELOG.md` |
| 6. 验证 | `bash manage.sh check` 全绿 + 功能实测 |

新增命令模板（manage.sh）：
```bash
  mycmd)
    arg="$2"; [ -z "$arg" ] && { echo "用法: notes mycmd <arg>"; exit 1; }
    python3 "$NOTES/scripts/my_script.py" "$arg" ;;
```

## 二、组件替换路径（升级就绪）

| 替换 | 做法 | 数据影响 |
|------|------|:---:|
| 换嵌入模型 | `embed.py` 改模型名 → `rm -rf .semantic && anote index-semantic --full` | 无 |
| 换向量库（ChromaDB 等） | 只改 `embed.py`（写）与 `ask.py::semantic_search`（读），CLI 接口不变 | 无 |
| 加 Web 外壳 | 新目录，只读 `src/` + `.semantic/`，写经 `anote commit` | 无 |
| 加知识编译层（wiki） | 新增 `wiki.py`，读 `src/` 写 `memory/` | 无 |

## 三、接口变更纪律

- 冻结格式（**永不破坏**）：`src/` 笔记+META、`memory/` 结构、`queue.md` 列结构
- 可重建派生物（随便改）：`.semantic/`、`00-index.tex`、`reviews/`
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
cd ~/Projects/Anote
git pull                        # 有远程时
./setup.sh                      # 自举（依赖/venv/索引/自检）
anote check                     # 全绿即完成
```
任何时刻 `src/` 完好 ⇒ 系统可 100% 重建。
