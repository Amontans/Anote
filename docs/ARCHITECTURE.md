# 架构文档（ARCHITECTURE）

## 设计原则

1. **单一真相源**：`src/` 的笔记是唯一不可再生数据；其余（索引/语义缓存/回顾/队列）全部可重建
2. **资产不绑定工具**：一切知识是 `.tex`/`.md`/`.bib`/PDF 纯文本；编辑器、AI、Web 外壳都是可替换的
3. **AI 可插拔**：AI 层只做"提议与草拟"，人做"确认"；换模型/助手不损失任何资产
4. **自动化 > 手动**：能由钩子/定时器/脚本做的，绝不要求人做
5. **接口先于实现**：所有数据格式与 CLI 有书面契约（`docs/INTERFACES.md`）
6. **数据自足**：配置/日志/MCP 注册/默认备份全部位于数据根 `.anote/`，项目仓库无用户数据

## 分层结构

```
┌────────────────────────────────────────────────┐
│  AI 层（可插拔）                                  │
│  Pi + DeepSeek：检索/精读填充/提炼/问答/回顾       │
├────────────────────────────────────────────────┤
│  命令层（唯一入口）                               │
│  anote（bash 编排，路径自动推导） → 42 py + 4 sh   │
├────────────────────────────────────────────────┤
│  业务层                                           │
│  src/anote/core.py（Config/Result/日志/路径）      │
│  src/anote/services/（一领域一模块，重模块懒加载）   │
├────────────────────────────────────────────────┤
│  数据层（纯文本，git 版本化）                      │
│  src/ memory/ books/ projects/ queue/roadmap/    │
│  refs.bib pdfs/ ebooks/ docs/registry.md         │
│  .anote/config+logs+external.json+backups        │
└────────────────────────────────────────────────┘
```

## 数据流（三级管线）

```
① 积累:  检索(--queue) → 下载(--dir pdfs --tex-note) → src/papers/精读笔记 → src/学科笔记
         ▲                                      │
         └── ask.py(关键词/混合检索) ← .semantic/ ←┘
② 编译:  周回顾(review.py) → 提炼 → memory/{insights,concepts,open-questions}
③ 成书:  anote book/chapter → books/<名>/ → latexmk 编译 PDF
└── 全程: pre-commit 自动索引+自检；git 提交；backup 推送/冷备
```

## 状态流（队列）

`📥待读 → 📖在读 → ✅已精读 → 🗄已归档`（+ check 一致性校验）

## 关键机制

| 机制 | 实现 | 目的 |
|------|------|------|
| 防遗忘 | check.py 8 项 + pre-commit 提示 + pre-push 门禁 | 结构不腐烂 |
| 省 token | ask.py 片段检索（grep/BM25/向量） | 问答不读全文 |
| 升级安全 | schema_version + 可重建派生物 | 换组件不换数据 |
| 备份 | git + `anote backup-create`（默认 `.anote/backups`） | 资产永不丢失 |
| 可移植 | 项目路径自动推导 + 数据根自足 | 任意目录 clone/拷贝均可用 |
