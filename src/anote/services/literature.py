"""文献检索领域服务：arXiv/Semantic Scholar/OpenAlex/Crossref 检索 + BibTeX/入队。

所有 provider 逻辑集中于此（search.py 薄适配器调用）。
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta

UA = {"User-Agent": "anote-literature/1.3 (academic research)"}

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


