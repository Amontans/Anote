#!/usr/bin/env python3
"""Unified academic literature search: arXiv | Semantic Scholar | OpenAlex | Crossref.

Usage examples:
  search.py --provider arxiv --query "retrieval augmented generation" --max 10
  search.py --provider openalex --query "large language models" --sort cited_by_count:desc --bib out.bib
  search.py --provider s2 --doi 10.48550/arXiv.2306.03307 --citations
  search.py --arxivid 2401.12345 --bib single.bib
  search.py --papers "2401.12345 2310.06825" --bib batch.bib
"""
import argparse
import os
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta

UA = {"User-Agent": "literature-search-skill/1.0 (academic research)"}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote import cli as _cli  # noqa: E402

def http_get(url, params=None, timeout=30, retries=2):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    last_err = None
    for i in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"HTTP request failed: {url} -> {last_err}")


def first_author(authors, n=3):
    a = [x for x in authors if x]
    if len(a) <= n:
        return " and ".join(a)
    return " and ".join(a[:n]) + " et al."


def arxiv_search(query, max_results, since_months=None, sort="relevance"):
    # arXiv API is Atom XML; fetch and parse minimal fields via regex-free approach
    import re
    base = "http://export.arxiv.org/api/query"
    q = urllib.parse.quote(query)
    sort_by = "submittedDate" if sort == "date" else "relevance"
    if since_months:
        d = date.today() - timedelta(days=30 * since_months)
        q += f"+AND+submittedDate:[{d.strftime('%Y%m%d')}000000+TO+*]"
    url = f"{base}?search_query={q}&start=0&max_results={max_results}&sortBy={sort_by}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        xml = r.read().decode("utf-8")
    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.S)
    out = []
    for e in entries:
        def g(tag):
            m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", e, re.S)
            return m.group(1).strip() if m else ""
        authors = re.findall(r"<name>(.*?)</name>", e)
        idm = re.search(r"<id>(.*?)</id>", e)
        aid = ""
        if idm:
            aid = idm.group(1).rstrip("/").split("/abs/")[-1]
        out.append({
            "source": "arXiv", "title": g("title").replace("\n ", "").strip(),
            "authors": authors, "year": g("published")[:4],
            "abstract": g("summary").replace("\n", " ").strip(),
            "url": f"https://arxiv.org/abs/{aid}", "arxiv_id": aid,
            "doi": g("arxiv:doi") or "",
        })
    return out


def s2_lookup(doi=None, arxivid=None):
    key = {"doi": doi} if doi else {"arxivId": arxivid}
    p = {**key, "fields": "title,authors,year,abstract,citationCount,externalIds,venue,url,openAccessPdf"}
    d = http_get("https://api.semanticscholar.org/graph/v1/paper", p)
    return [{
        "source": "Semantic Scholar", "title": d.get("title", ""),
        "authors": [a.get("name", "") for a in d.get("authors", [])],
        "year": str(d.get("year", "")), "abstract": d.get("abstract", "") or "",
        "citations": d.get("citationCount", 0),
        "url": d.get("url", ""), "venue": d.get("venue", ""),
        "doi": (d.get("externalIds") or {}).get("DOI", ""),
        "arxiv_id": (d.get("externalIds") or {}).get("ArXiv", ""),
        "pdf": (d.get("openAccessPdf") or {}).get("url", ""),
    }]


def s2_citations(doi=None, arxivid=None, limit=20):
    key = {"doi": doi} if doi else {"arxivId": arxivid}
    p = {**key, "fields": "title,year,authors,externalIds", "limit": limit}
    d = http_get("https://api.semanticscholar.org/graph/v1/paper/citations", p)
    return [{
        "title": c.get("citingPaper", {}).get("title", ""),
        "year": str(c.get("citingPaper", {}).get("year", "")),
        "authors": [a.get("name", "") for a in c.get("citingPaper", {}).get("authors", [])],
        "doi": (c.get("citingPaper", {}).get("externalIds") or {}).get("DOI", ""),
    } for c in d.get("data", [])]


def openalex_search(query, max_results, since=None, sort="relevance_score:desc"):
    p = {"search": query, "per-page": max_results, "mailto": "research@example.com",
         "sort": sort}
    if since:
        p["filter"] = f"from_publication_date:{since}-01-01"
    d = http_get("https://api.openalex.org/works", p)
    out = []
    for w in d.get("results", []):
        out.append({
            "source": "OpenAlex", "title": w.get("title", ""),
            "authors": [a["author"]["display_name"] for a in w.get("authorships", [])],
            "year": str(w.get("publication_year", "")),
            "abstract": (w.get("abstract_inverted_index") or {}).__class__.__name__,
            "citations": w.get("cited_by_count", 0),
            "url": w.get("doi") or w.get("id", ""), "venue": (w.get("primary_location") or {}).get("source", {}) and ((w.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
            "doi": w.get("doi", ""), "openalex_id": w.get("id", ""),
        })
    return out


def crossref_doi(doi):
    d = http_get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}")
    m = d["message"]
    return [{
        "source": "Crossref", "title": (m.get("title") or [""])[0],
        "authors": [f"{a.get('given','')} {a.get('family','')}".strip() for a in m.get("author", [])],
        "year": str((m.get("issued") or {}).get("date-parts", [[""]])[0][0]),
        "abstract": re_sub(m.get("abstract", "")), "citations": None,
        "url": m.get("URL", ""), "venue": (m.get("container-title") or [""])[0],
        "doi": m.get("DOI", ""),
    }]


def re_sub(s):
    import re
    return re.sub(r"<[^>]+>", "", s or "").strip()


def to_bibtex(papers):
    entries = []
    for i, p in enumerate(papers):
        key = f"{'arXiv' if p.get('arxiv_id') else 'doi'}_{i}"
        fields = []
        if p.get("title"):
            fields.append(("title", p["title"]))
        if p.get("authors"):
            fields.append(("author", first_author(p["authors"], 12)))
        if p.get("year"):
            fields.append(("year", p["year"]))
        if p.get("venue") and p["venue"] not in ("", "arXiv"):
            fields.append(("journal", p["venue"]))
        if p.get("arxiv_id"):
            fields.append(("eprint", p["arxiv_id"]))
            fields.append(("archiveprefix", "arXiv"))
        if p.get("doi"):
            fields.append(("doi", p["doi"]))
        if p.get("abstract"):
            ab = p["abstract"][:400].replace("&", r"\&")
            fields.append(("abstract", ab))
        if p.get("url"):
            fields.append(("url", p["url"]))
        body = ",\n  ".join(f"{k} = {{{v}}}" for k, v in fields)
        entry_type = "article" if p.get("arxiv_id") else "misc"
        entries.append(f"@{entry_type}{{{key},\n  {body}\n}}")
    return "\n\n".join(entries) + "\n"


def enqueue(queue_path, papers):
    """把检索结果追加到待读队列 queue.md（Markdown 表格）"""
    rows = []
    for p in papers:
        key = p.get("arxiv_id") or p.get("doi") or p.get("url")
        rows.append(f"| \U0001F4E5 | {date.today().isoformat()} | {p.get('title', '')[:50]} | {key} | \u2014 |")
    if not rows:
        return 0
    with open(queue_path, encoding="utf-8") as f:
        text = f.read()
    marker = "<!-- 活动队列 -->"
    if marker not in text:
        # 在表头行后插入
        text = text.replace("|------|", "|------|\n" + "\n".join(rows), 1)
    else:
        text = text.replace(marker, marker + "\n" + "\n".join(rows), 1)
    with open(queue_path, "w", encoding="utf-8") as f:
        f.write(text)
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description="Academic literature search")
    ap.add_argument("--queue", help="追加到论文待读队列（如 ~/Projects/notes/queue.tex）")
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
    a = ap.parse_args()

    papers = []
    if a.citations:
        for c in s2_citations(doi=a.doi, arxivid=a.arxivid, limit=a.max):
            print(f"[{c['year']}] {c['title']} — {first_author(c['authors'])}\n  doi: {c['doi'] or '-'}")
        sys.exit(0)
    if a.doi:
        papers = crossref_doi(a.doi)
    elif a.arxivid:
        papers = arxiv_search(f"id:{a.arxivid}", 1)
    elif a.papers:
        for pid in a.papers:
            if pid.startswith("10."):
                papers += crossref_doi(pid)
            else:
                papers += arxiv_search(f"id:{pid}", 1)
    elif a.provider == "arxiv":
        papers = arxiv_search(a.query, a.max, since_months=a.since_months, sort=a.sort)
    elif a.provider == "s2":
        papers = s2_lookup(doi=a.query) if a.query.startswith("10.") else []
        if not papers:
            print("s2 provider: 请用 --doi 查询；或用 openalex/arxiv 做关键词检索。")
            sys.exit(1)
    elif a.provider == "openalex":
        papers = openalex_search(a.query, a.max, since=a.since, sort=a.sort)
    elif a.provider == "crossref":
        papers = crossref_doi(a.query) if a.query.startswith("10.") else []

    if not papers:
        print("未找到结果。")
        sys.exit(1)

    # console table
    for i, p in enumerate(papers, 1):
        cites = f" 引用 {p.get('citations')}" if p.get("citations") else ""
        print(f"{i}. [{p['year']}] {p['title']}{cites}")
        print(f"   {first_author(p['authors'])}")
        print(f"   {p.get('url') or p.get('doi')}")
        if p.get("abstract") and not p.get("abstract", "").startswith("dict"):
            print(f"   {p['abstract'][:180]}...")
    print(f"\n共 {len(papers)} 条。加 --bib out.bib 可导出 BibTeX。")

    if a.bib:
        with open(a.bib, "w") as f:
            f.write(to_bibtex(papers))
        print(f"BibTeX 已写入 {a.bib}")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        print(f"JSON 已写入 {a.json}")
    if a.queue:
        n = enqueue(os.path.expanduser(a.queue), papers)
        print(f"已将 {n} 条加入待读队列: {a.queue}")


if __name__ == "__main__":
    sys.exit(_cli.run(main))
