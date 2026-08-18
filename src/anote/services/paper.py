"""写作输出领域服务（v1.10）：论文素材聚合 + 骨架生成（经 Pi）。

流程: 主题 → 检索相关笔记(BM25/向量) + 引用 + wiki 主题页 + 反链
      → 素材包(materials.md) → 经 Pi 生成论文骨架(.tex)
"""
from __future__ import annotations

from pathlib import Path

from ..core import ai_ask
from .bib import BibService
from .notes import NotesService
from .retrieval import RetrievalService

TYPES = {"论文": "research", "综述": "survey", "开题": "proposal"}

SKELETON_TMPL = """%% ===== 论文骨架（anote paper 生成，人工填充）=====
%% 主题: {topic} | 类型: {type_cn} | 生成: {date}
\\documentclass[11pt]{{ctexart}}
\\usepackage[margin=2.5cm]{{geometry}}
\\usepackage{{amsmath,amssymb,graphicx}}
\\usepackage[colorlinks=true]{{hyperref}}

\\title{{{topic}}}
\\author{{作者}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle

\\begin{{abstract}}
%% 五句法则: 背景→问题→方法→结果→影响
\\end{{abstract}}

\\section{{引言}}
%% 背景→任务→已有工作→gap→贡献列表（3条）

\\section{{相关工作}}
%% 分主题小节；每组"共同局限"收尾

\\section{{方法}}
%% 架构图 + 记号表 + 各组件

\\section{{实验}}
%% 设置/主结果表/消融/分析

\\section{{结论}}
%% 总结 + 局限 + 未来工作

%% 引用: \\cite{{key}}（refs.bib 已有条目见 materials.md）
\\bibliographystyle{{unsrt}}
\\bibliography{{refs}}
\\end{{document}}
"""


def collect_materials(topic: str, data: Path, top: int = 5) -> dict:
    """聚合主题相关素材（纯逻辑，可单测）。"""
    materials = {"notes": [], "refs": [], "wiki": [], "backlinks": []}
    # ① 相关笔记（混合检索；无 fastembed 时 BM25 兜底）
    rels = []
    try:
        ret = RetrievalService(data)
        if ret.sem.has_index():
            for chunk, score, src in ret.retrieve(topic, top=top):
                rels.append(chunk.get("path", "").replace(str(data) + "/", ""))
    except Exception:  # noqa: BLE001
        pass
    if not rels:
        try:  # BM25 兜底（零依赖）
            import json
            from .retrieval import BM25Index
            meta = data / ".semantic" / "chunks.json"
            if meta.exists():
                chunks = json.loads(meta.read_text(encoding="utf-8")).get("chunks", [])
                scores = BM25Index(chunks).score(topic)
                for i in sorted(range(len(chunks)), key=lambda i: -scores[i])[:top]:
                    if scores[i] > 0:
                        rels.append(chunks[i].get("path", "").replace(str(data) + "/", ""))
        except Exception:  # noqa: BLE001
            pass
    for rel in rels:
        if rel and rel not in materials["notes"]:
            materials["notes"].append(rel)
    # ② 引用（refs.bib 关键词匹配）
    try:
        bib = BibService(data)
        t = topic.lower()
        for key in bib.keys():
            if t in key.lower():
                materials["refs"].append(key)
    except Exception:  # noqa: BLE001
        pass
    # ③ wiki 主题页（标题含主题词）
    wiki_dir = data / "wiki"
    if wiki_dir.is_dir():
        for p in sorted(wiki_dir.glob("*.md")):
            if t in p.stem.lower():
                materials["wiki"].append(str(p.relative_to(data)))
    return materials


def generate(topic: str, type_cn: str, materials: dict, data: Path, use_ai: bool = True) -> tuple[Path, str]:
    """生成骨架 → (路径, 说明)。"""
    out_dir = data / "projects" / topic
    out_dir.mkdir(parents=True, exist_ok=True)
    tex = out_dir / "paper.tex"
    md = out_dir / "materials.md"

    # 素材包
    md.write_text(
        f"# 素材包 · {topic}\n\n## 相关笔记\n" +
        "\n".join(f"- {n}" for n in materials["notes"]) +
        "\n\n## 相关引用（refs.bib）\n" +
        "\n".join(f"- \\cite{{{k}}}" for k in materials["refs"]) +
        "\n\n## wiki 主题页\n" +
        "\n".join(f"- {w}" for w in materials["wiki"]) + "\n",
        encoding="utf-8")

    if use_ai:
        prompt = (
            f"你是学术写作助手。请为《{topic}》（{type_cn}）生成 LaTeX 论文骨架，"
            f"包含: 引言（背景/问题/贡献列表）、相关工作（3-4 个主题）、方法、实验设置、结论。\n"
            f"可用素材: 相关笔记 {materials['notes'][:5]}，引用 {materials['refs'][:10]}。\n"
            f"输出完整的 .tex（用 ctexart + hyperref），结构清晰，方法部分可留占位。"
        )
        r = ai_ask(prompt)
        if r.ok and r.stdout.strip():
            content = r.stdout
            note = "（经 Pi 生成，请人工校对）"
        else:
            content = SKELETON_TMPL.format(topic=topic, type_cn=type_cn,
                                            date=__import__("datetime").date.today().isoformat())
            note = "（Pi 调用失败，已用内置模板兜底）"
    else:
        content = SKELETON_TMPL.format(topic=topic, type_cn=type_cn,
                                        date=__import__("datetime").date.today().isoformat())
        note = "（--no-ai 内置模板）"
    tex.write_text(content, encoding="utf-8")
    return tex, note
