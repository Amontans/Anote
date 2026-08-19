"""检索质量领域服务（v1.9 / v1.16 性能优化）：
BM25 词法 + 向量语义混合检索 + 轻量重排。

- BM25：倒排索引持久化到 .semantic/bm25.json；只计算命中查询词的文档
- 混合：向量 top-K ∪ BM25 top-K → 归一化加权融合（默认 0.6 向量 / 0.4 词法）
- 轻量重排：查询词命中密度加成（CPU 友好）
"""
from __future__ import annotations

import hashlib
import json
import math
import re
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
    """倒排索引版 BM25；可持久化到 .semantic/bm25.json。

    内存结构只保留 postings 与文档长度，查询复杂度约等于查询词命中项数。
    """

    SCHEMA = 1

    def __init__(self, chunks: list[dict] | None = None):
        self.doc_len: list[int] = []
        self.postings: dict[str, list[tuple[int, int]]] = {}
        self.df: dict[str, int] = {}
        self.n = 0
        self.avgdl = 1.0
        if chunks is not None:
            self.build(chunks)

    def build(self, chunks: list[dict]) -> None:
        self.doc_len = []
        self.postings = {}
        self.df = {}
        for i, c in enumerate(chunks):
            toks = tokenize(c.get("text", ""))
            tf = Counter(toks)
            self.doc_len.append(len(toks))
            for t, count in tf.items():
                self.postings.setdefault(t, []).append((i, count))
                self.df[t] = self.df.get(t, 0) + 1
        self.n = len(chunks)
        self.avgdl = (sum(self.doc_len) / self.n) if self.n else 1.0

    def score(self, query: str, k1: float = 1.5, b: float = 0.75) -> list[float]:
        scores = [0.0] * self.n
        for t in set(tokenize(query)):
            if t not in self.postings:
                continue
            idf = math.log(1 + (self.n - self.df.get(t, 0) + 0.5) / (self.df.get(t, 0) + 0.5))
            for doc_id, tf in self.postings[t]:
                dl = self.doc_len[doc_id]
                scores[doc_id] += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / self.avgdl))
        return scores

    def save(self, path: Path, signature: str) -> None:
        data = {
            "schema_version": self.SCHEMA,
            "signature": signature,
            "doc_len": self.doc_len,
            "df": self.df,
            "postings": {t: v for t, v in self.postings.items()},
        }
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path, signature: str) -> "BM25Index":
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") != cls.SCHEMA or data.get("signature") != signature:
            raise ValueError("BM25 缓存签名/版本不匹配")
        idx = cls()
        idx.doc_len = [int(x) for x in data.get("doc_len", [])]
        idx.df = {str(k): int(v) for k, v in data.get("df", {}).items()}
        idx.postings = {str(k): [(int(i), int(c)) for i, c in v]
                        for k, v in data.get("postings", {}).items()}
        idx.n = len(idx.doc_len)
        idx.avgdl = (sum(idx.doc_len) / idx.n) if idx.n else 1.0
        return idx


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
        data = json.loads(meta.read_text(encoding="utf-8"))
        return data.get("chunks", []) if data.get("schema_version", 1) == 1 else []

    def _chunks_signature(self, chunks: list[dict]) -> str:
        sig = [{"path": c.get("path"), "mtime": c.get("mtime"), "text": c.get("text", "")}
               for c in chunks]
        return hashlib.sha256(json.dumps(sig, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

    def _bm25(self, chunks: list[dict]) -> BM25Index:
        cache = self.data / ".semantic" / "bm25.json"
        signature = self._chunks_signature(chunks)
        if cache.exists():
            try:
                return BM25Index.load(cache, signature)
            except Exception:  # noqa: BLE001
                pass
        idx = BM25Index(chunks)
        try:
            idx.save(cache, signature)
        except OSError:
            pass
        return idx

    def retrieve(self, query: str, top: int = 5, hybrid: bool = True) -> list[tuple[dict, float, str]]:
        """→ [(chunk, score, source)]，source ∈ {vector, bm25, hybrid}。"""
        chunks = self._load_chunks()
        if not chunks or not self.sem.has_index():
            return []
        n = len(chunks)
        # chunk 对象可能来自不同 json.load，用 (path, text) 建立稳定索引
        key_to_idx: dict[tuple, int] = {}
        for i, c in enumerate(chunks):
            key_to_idx.setdefault((c.get("path"), c.get("text")), i)

        bm = self._bm25(chunks)
        bm_scores = bm.score(query)

        vec = [0.0] * n
        vector_hits: list[tuple[dict, float]] = []
        if hybrid:
            vector_hits = self.sem.search(query, top=min(top * 3, n) or n)
            for chunk, score in vector_hits:
                idx = key_to_idx.get((chunk.get("path"), chunk.get("text")))
                if idx is not None:
                    vec[idx] = score

        # 候选集 = 向量 top-K ∪ BM25 top-K（避免对全库做无意义融合排序）
        candidates: set[int] = set()
        for chunk, _ in vector_hits:
            idx = key_to_idx.get((chunk.get("path"), chunk.get("text")))
            if idx is not None:
                candidates.add(idx)
        bm_candidates = sorted(range(n), key=lambda i: -bm_scores[i])[:top * 3]
        candidates.update(bm_candidates)
        if not candidates:
            return []

        def norm(scores: list[float], idxs: set[int]) -> list[float]:
            mx = max((scores[i] for i in idxs), default=0.0)
            if mx <= 0:
                return [0.0] * n
            return [s / mx for s in scores]

        vn = norm(vec, candidates)
        bn = norm(bm_scores, candidates)
        q_tokens = set(tokenize(query))
        ranked = []
        for i in candidates:
            final = vn[i] * self.vec_weight + bn[i] * (1 - self.vec_weight)
            text = chunks[i].get("text", "")
            hit = sum(1 for t in q_tokens if t in text.lower())
            if hit:
                final += 0.05 * hit
            ranked.append((final, i))
        ranked.sort(key=lambda x: -x[0])
        out = []
        for score, i in ranked[:top]:
            src = "vector" if vec[i] > bm_scores[i] else "bm25"
            out.append((chunks[i], score, src))
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
