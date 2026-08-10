#!/usr/bin/env python3
"""anote search —— 文献检索（薄适配器；逻辑在 services/literature.py）。

接口声明（契约）:
    输入: --provider arxiv|s2|openalex|crossref --query ... [--max N] [--bib 文件] [--queue 文件] [--json 文件] [--doi] [--arxivid] [--papers] [--citations]
    输出: stdout=结果表；退出码 0/1
    副作用: --bib/--json/--queue 写文件
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.services import literature as lit  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="文献检索")
    ap.add_argument("--provider", default="arxiv", choices=["arxiv", "s2", "openalex", "crossref"])
    ap.add_argument("--query", default="")
    ap.add_argument("--max", type=int, default=5)
    ap.add_argument("--since", type=int)
    ap.add_argument("--since-months", type=int)
    ap.add_argument("--sort", default="relevance")
    ap.add_argument("--bib")
    ap.add_argument("--json")
    ap.add_argument("--doi")
    ap.add_argument("--arxivid")
    ap.add_argument("--papers", nargs="*")
    ap.add_argument("--citations", action="store_true")
    ap.add_argument("--queue")
    a = ap.parse_args()

    if a.citations:
        for c in lit.s2_citations(doi=a.doi, arxivid=a.arxivid, limit=a.max):
            print(f"[{c['year']}] {c['title']} — {lit.first_author(c['authors'])}\n  doi: {c['doi'] or '-'}")
        return 0
    if a.doi:
        papers = lit.crossref_doi(a.doi)
    elif a.arxivid:
        papers = lit.arxiv_search(f"id:{a.arxivid}", 1)
    elif a.papers:
        papers = []
        for pid in a.papers:
            papers += lit.crossref_doi(pid) if pid.startswith("10.") else lit.arxiv_search(f"id:{pid}", 1)
    elif a.provider == "arxiv":
        papers = lit.arxiv_search(a.query, a.max, since_months=a.since_months, sort=a.sort)
    elif a.provider == "openalex":
        papers = lit.openalex_search(a.query, a.max, since=a.since, sort=a.sort)
    elif a.provider == "s2":
        papers = lit.s2_lookup(doi=a.query) if a.query.startswith("10.") else []
    else:
        papers = lit.crossref_doi(a.query) if a.query.startswith("10.") else []

    if not papers:
        print("未找到结果。")
        return 0
    for i, p in enumerate(papers, 1):
        cites = f" 引用 {p.get('citations')}" if p.get("citations") else ""
        print(f"{i}. [{p['year']}] {p['title']}{cites}")
        print(f"   {lit.first_author(p['authors'])}")
        print(f"   {p.get('url') or p.get('doi')}")
        if p.get("abstract") and not str(p.get("abstract")).startswith("dict"):
            print(f"   {p['abstract'][:180]}...")
    print(f"\n共 {len(papers)} 条。加 --bib out.bib 可导出 BibTeX。")
    if a.bib:
        open(os.path.expanduser(a.bib), "w", encoding="utf-8").write(lit.to_bibtex(papers))
        print(f"BibTeX 已写入 {a.bib}")
    if a.json:
        json.dump(papers, open(os.path.expanduser(a.json), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if a.queue:
        n = lit.enqueue(os.path.expanduser(a.queue), papers)
        print(f"已将 {n} 条加入待读队列: {a.queue}")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
