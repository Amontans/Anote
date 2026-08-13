#!/usr/bin/env python3
"""anote ask —— 知识库问答：grep 片段检索 + --semantic 语义检索。

接口声明（契约）:
    输入: query [--smart] [--semantic] [--top N] [--maxchars N]
    输出: stdout=命中片段；退出码 0/1
    副作用: 无
"""
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.semantic import SemanticService  # noqa: E402

STOP = {"的", "了", "是", "在", "我", "有", "和", "与", "及", "而", "不", "或", "对", "从", "等",
        "这", "那", "被", "把", "于", "为", "还", "也", "将", "你", "他", "她", "它们",
        "什么", "为什么", "怎么", "如何", "哪个", "哪些", "怎样", "能否", "解释", "一下",
        "总结", "概括", "关于", "请问", "给我", "帮忙", "帮助", "学习", "科研", "论文", "笔记",
        "方法", "问题", "内容", "这个", "那个", "需要", "应该", "可以", "可能", "是否",
        "有没有", "我想", "我要", "我觉得", "我认为", "其实", "也就是", "比如", "例如"}


def extract_keywords(question: str) -> tuple[list, list]:
    q = question
    for s in sorted(STOP, key=len, reverse=True):
        q = q.replace(s, " ")
    zh = re.findall(r"[\u4e00-\u9fff]{2,6}", q)
    en = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", question)
    short = [w for w in zh if len(w) <= 4] or zh
    return short[:5], en[:5]


def rg(pattern: str, root: str) -> list[str]:
    try:
        r = subprocess.run(["rg", "--no-ignore", "-l", "-i", pattern, ".",
                            "-g", "!.venv/**", "-g", "!.semantic/**", "-g", "!.git/**",
                            "-g", "*.tex", "-g", "*.md", "-g", "*.txt",
                            "-g", "!00-index.tex", "-g", "!README.md"],
                           capture_output=True, text=True, timeout=30, cwd=root)
        return [l for l in r.stdout.splitlines() if l.strip()]
    except Exception:  # noqa: BLE001
        return []


def snippets(path: str, pattern: str, maxchars: int) -> list[str]:
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


def _in_layer(path: str, layer: str) -> bool:
    """分层过滤：notes=src/memory/wiki；docs=pdfs/ebooks。"""
    if layer == "notes":
        return path.startswith(("src/", "memory/", "wiki/"))
    if layer == "docs":
        return path.startswith(("pdfs/", "ebooks/"))
    return True


def _log_failed(query: str, root: str) -> None:
    """无命中查询记入 memory/query-failures.log（评测闭环）。"""
    from datetime import date
    log = Path(root) / "memory" / "query-failures.log"
    try:
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"{date.today().isoformat()} | {query}\n")
    except Exception:  # noqa: BLE001
        pass


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("用法: anote ask \"<问题>\" [--smart] [--semantic]")
        return 1
    # 提取 query：跳过带值 flag（--top/--maxchars/--layer）的值
    value_flags = {"--top", "--maxchars", "--layer"}
    i = 0
    query = ""
    while i < len(args):
        a = args[i]
        if a in value_flags:
            i += 2
            continue
        if not a.startswith("--"):
            query = a
            break
        i += 1
    if not query:
        print("用法: anote ask \"<问题>\" [--smart] [--semantic] [--bm25] [--layer notes|docs]")
        return 1
    smart = "--smart" in args
    semantic = "--semantic" in args
    top = 5
    if "--top" in args:
        i = args.index("--top")
        if i + 1 < len(args):
            top = int(args[i + 1])
    maxchars = 6000
    if "--maxchars" in args:
        i = args.index("--maxchars")
        if i + 1 < len(args):
            maxchars = int(args[i + 1])
    root = str(Config.load().data_dir)

    if semantic:
        from anote.services.retrieval import RetrievalService
        bm25_only = "--bm25" in args
        layer = None
        if "--layer" in args:
            i = args.index("--layer")
            if i + 1 < len(args):
                layer = args[i + 1]
        svc = RetrievalService(Config.load().data_dir)
        if not svc.sem.has_index():
            print("尚未建语义索引：先运行 anote index-semantic")
            return 1
        fetch = top * 6 if layer else top
        hits = svc.retrieve(query, fetch, hybrid=not bm25_only)
        if layer:
            hits = [h for h in hits
                    if _in_layer(os.path.relpath(h[0].get("path", ""), root), layer)][:top]
        if not hits:
            print("无结果")
            _log_failed(query, root)
            return 1
        label = "BM25 词法检索" if bm25_only else "混合检索（向量+BM25+重排）"
        print(f"{label}: {query}   范围: {root}\n")
        for i, (chunk, score, src) in enumerate(hits, 1):
            print(f"{i}. [{score:.3f} {src}] {os.path.relpath(chunk['path'], root)}")
            print(f"   {chunk['text'][:200]}")
        print("\n（片段为最相关内容）")
        return 0

    patterns = extract_keywords(query) if smart else ([query], [])
    keywords = [p for p in patterns[0] + patterns[1] if p]
    print(f"检索词: {' '.join(keywords)}  范围: {root}\n")
    hits = {}
    for p in keywords:
        for f in rg(p, root):
            hits.setdefault(f, 0)
            hits[f] += 1
    ranked = sorted(hits, key=hits.get, reverse=True)[:top]
    if not ranked:
        print("无命中。换个关键词，或直接让 AI 读某个文件。")
        _log_failed(query, root)
        return 0
    print(f"命中 {len(hits)} 个文件，展示前 {len(ranked)} 个：\n" + "=" * 60)
    for f in ranked:
        print(f"\n## {f}  (命中 {hits[f]} 次)")
        for ln in snippets(f, keywords[0], maxchars):
            print(ln)
    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
