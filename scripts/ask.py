#!/usr/bin/env python3
"""知识库检索问答助手（解决"每次读全文浪费 token"问题）。

原理: 先用 ripgrep 在 ~/Projects/notes 中定位命中片段，只输出相关片段（可控 token 量），
      AI 基于片段组织回答，而不是读全文。

用法:
  ask.py "注意力机制"                    # 直接关键词
  ask.py --smart "什么是检索增强生成？"    # 自然语言问题，自动提取词
  ask.py "图神经网络" --top 6 --maxchars 6000   # 控制输出量
  ask.py --notes ~/Projects/notes "卷积"          # 指定库位置
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anote_config import data_dir as _cfg_data_dir
DEFAULT_NOTES = _cfg_data_dir()
STOP = set("的了是在我有和与及而不或对从等这那被把于为还也将你他她它们什么为什么怎么如何哪个哪些哪些什么怎样能否为什么解释一下总结概括关于请问给我帮忙帮助学习科研论文笔记方法问题内容这个那个一种一种种个每个需要应该可以可能是否有没有请问我想我要我觉得我认为其实也就是比如例如比如".strip())


def extract_keywords(question):
    """从自然语言问题提取检索词：先剥离停用词，再取 2-6 字中文串 + 3+ 字母英文词。"""
    q = question
    for s in sorted(STOP, key=len, reverse=True):
        q = q.replace(s, " ")
    zh = re.findall(r"[\u4e00-\u9fff]{2,6}", q)
    en = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", question)
    short = [w for w in zh if len(w) <= 4] or zh
    return short[:5], en[:5]


def rg(pattern, root):
    try:
        r = subprocess.run(
            ["rg", "-l", "-i", pattern, root, "-g", "*.tex", "-g", "*.md", "-g", "!00-index.tex", "-g", "!README.md"],
            capture_output=True, text=True, timeout=30)
        return [l for l in r.stdout.splitlines() if l.strip()]
    except Exception:  # noqa: BLE001
        return []


def snippets(path, pattern, maxchars):
    """返回该文件中命中片段（带行号），总长不超过 maxchars。"""
    try:
        r = subprocess.run(["rg", "-n", "-i", "-C", "2", pattern, path],
                           capture_output=True, text=True, timeout=20)
        lines = r.stdout.splitlines()
    except Exception:  # noqa: BLE001
        return []
    out, total = [], 0
    for ln in lines:
        if total + len(ln) + 1 > maxchars:
            break
        out.append(ln)
        total += len(ln) + 1
    return out


def semantic_search(query, top, notes):
    """语义向量检索：加载缓存 → 嵌入问题 → 余弦 top-k。返回 [(chunk, score)] 或 None（未建索引）。"""
    cache = os.path.join(notes, ".semantic")
    meta, vecp = os.path.join(cache, "chunks.json"), os.path.join(cache, "vectors.npy")
    if not (os.path.exists(meta) and os.path.exists(vecp)):
        return None
    import json
    import numpy as np
    from fastembed import TextEmbedding
    data = json.load(open(meta, encoding="utf-8"))
    chunks = data["chunks"] if isinstance(data, dict) else data
    vecs = np.load(vecp)
    model = TextEmbedding(model_name="BAAI/bge-small-zh-v1.5")
    qv = np.asarray(next(model.embed([query])), dtype=np.float32)
    sims = (vecs @ qv) / ((np.linalg.norm(vecs, axis=1) + 1e-9) * (np.linalg.norm(qv) + 1e-9))
    idxs = np.argsort(-sims)[:top]
    return [(chunks[i], float(sims[i])) for i in idxs]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="检索词（用引号括起）")
    ap.add_argument("--smart", action="store_true", help="query 是自然语言问题，自动提取词")
    ap.add_argument("--semantic", action="store_true", help="语义向量检索（需先 notes index-semantic）")
    ap.add_argument("--top", type=int, default=5, help="最多取几个文件")
    ap.add_argument("--maxchars", type=int, default=6000, help="每个文件的片段上限字符")
    ap.add_argument("--notes", default=DEFAULT_NOTES)
    a = ap.parse_args()

    root = os.path.expanduser(a.notes)
    if a.semantic:
        hits = semantic_search(a.query, a.top, root)
        if hits is None:
            print("尚未建语义索引：先运行  notes index-semantic")
            sys.exit(1)
        print(f"语义检索: {a.query}   范围: {root}\n")
        for i, (chunk, score) in enumerate(hits, 1):
            print(f"{i}. [{score:.3f}] {os.path.relpath(chunk['path'], root)}")
            print(f"   {chunk['text'][:200]}")
        print("\n（片段为语义最相关内容，AI 基于片段回答）")
        sys.exit(0)
    if a.smart:
        zh, en = extract_keywords(a.query)
        patterns = zh + en
    else:
        patterns = [a.query]
    if not patterns:
        print("未提取到有效检索词")
        sys.exit(1)

    print(f"检索词: {' '.join(patterns)}  范围: {root}\n")
    hits = {}
    for p in patterns:
        for f in rg(p, root):
            hits.setdefault(f, 0)
            hits[f] += 1
    ranked = sorted(hits, key=hits.get, reverse=True)[:a.top]
    if not ranked:
        print("无命中。换个关键词，或直接让我读某个文件。")
        sys.exit(0)

    print(f"命中 {len(hits)} 个文件，展示前 {len(ranked)} 个：\n" + "=" * 60)
    for f in ranked:
        print(f"\n## {f}  (命中 {hits[f]} 次)")
        for ln in snippets(os.path.join(root, f), patterns[0], a.maxchars):
            print(ln)
    print("\n" + "=" * 60)
    print("（以上为检索片段。AI 基于片段回答；需要全文时再指定文件精读。）")


if __name__ == "__main__":
    main()
