"""检索质量领域服务（v1.9）：BM25 词法 + 向量语义混合检索 + 轻量重排。

- BM25：基于 .semantic 块语料的词法打分（无外部依赖，中文 2-gram 分词）
- 混合：向量余弦 + BM25 加权融合（默认 0.6 向量 / 0.4 词法）
- 轻量重排：查询词命中密度加成（替代重型的交叉编码器，CPU 友好）
"""
from __future__ import annotations

import math
import re
import string
from collections import Counter, defaultdict
from pathlib import Path

from .semantic import SemanticService

TOKEN_RE = re.compile(r"[\u4e00-\u9fff]{1,4}|[A-Za-z][A-Za-z0-9\-]{2,}")


def tokenize(text: str) -> list[str]:
    """中文 1-4 字连续块 + 英文词。"""
    return TOKEN_RE.findall(text.lower())


def bm25_score(query_terms: list[str], term_freq: Counter, dl: float,
               avgdl: float, n: int, df: dict, k1: float = 1.5, b: float = 0.75) -> float:
    score = 0.0
    for t in set(query_terms):
        tf = term_freq.get(t, 0)
        if tf == 0:
            continue
        idf = math.log(1 + (n - df.get(t, 0) + 0.5) / (df.get(t, 0) + 0.5))
        score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avgdl))
    return score


class BM25Index:
    """基于 chunk 语料的 BM25 索引（构建于内存）。"""

    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.doc_len: list[int] = []
        self.term_freqs: list[Counter] = []
        self.df: Counter = Counter()
        for c in chunks:
            toks = tokenize(c.get("text", ""))
            tf = Counter(toks)
            self.doc_len.append(len(toks))
            self.term_freqs.append(tf)
            for t in set(toks):
                self.df[t] += 1
        self.n = len(chunks)
        self.avgdl = (sum(self.doc_len) / self.n) if self.n else 1.0

    def score(self, query: str) -> list[float]:
        q = tokenize(query)
        return [bm25_score(q, self.term_freqs[i], self.doc_len[i], self.avgdl, self.n, self.df)
                for i in range(self.n)]


class RetrievalService:
    """混合检索：向量 top-K ∪ BM25 top-K → 加权融合 → 轻量重排。"""

    def __init__(self, data_dir: Path, vec_weight: float = 0.6):
        self.data = Path(data_dir)
        self.sem = SemanticService(self.data)
        self.vec_weight = vec_weight

    def _load_chunks(self) -> list[dict]:
        meta = self.data / ".semantic" / "chunks.json"
        if not meta.exists():
            return []
        import json
        data = json.loads(meta.read_text(encoding="utf-8"))
        return data.get("chunks", []) if data.get("schema_version", 1) == 1 else []

    def retrieve(self, query: str, top: int = 5, hybrid: bool = True) -> list[tuple[dict, float, str]]:
        """→ [(chunk, score, source)]，source ∈ {vector, bm25, hybrid}。"""
        chunks = self._load_chunks()
        if not chunks or not self.sem.has_index():
            return []
        n = len(chunks)
        # 向量分
        vec = [0.0] * n
        if hybrid:
            hits = self.sem.search(query, top=min(top * 3, n) or n)
            for chunk, score in hits:
                idx = chunks.index(chunk) if chunk in chunks else -1
                if idx >= 0:
                    vec[idx] = score
        # BM25 分
        bm = BM25Index(chunks).score(query)
        # 归一化融合
        def norm(v):
            mx = max(v) if v and max(v) > 0 else 1.0
            return [x / mx for x in v]
        vn, bn = norm(vec), norm(bm)
        final = [(vn[i] * self.vec_weight + bn[i] * (1 - self.vec_weight)) for i in range(n)]
        # 轻量重排：查询词命中密度加成
        q_tokens = set(tokenize(query))
        for i in range(n):
            text = chunks[i].get("text", "")
            hit = sum(1 for t in q_tokens if t in text.lower())
            if hit:
                final[i] += 0.05 * hit
        ranked = sorted(range(n), key=lambda i: -final[i])[:top]
        out = []
        for i in ranked:
            src = "vector" if vec[i] > bm[i] else "bm25"
            out.append((chunks[i], final[i], src))
        return out

    def self_hit_eval(self, k: int = 3, sample: int = 20) -> dict:
        """自命中评测：以笔记标题为查询，期望命中该笔记自身（top-k 命中率）。"""
        from .notes import NotesService
        notes = [n for n in NotesService(self.data).scan() if n.meta]
        import random
        random.seed(42)
        sample_notes = random.sample(notes, min(sample, len(notes)))
        hit = 0
        for n in sample_notes:
            results = self.retrieve(n.title, top=k)
            if any(n.rel in r[0].get("path", "") for r in results):
                hit += 1
        return {"sample": len(sample_notes), "hit_top" + str(k): hit,
                "hit_rate": round(hit / max(1, len(sample_notes)), 3)}
