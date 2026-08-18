"""语义检索领域服务：切块/建索引/检索（embed.py 与 ask.py 共用）。

存储: .semantic/chunks.json {schema_version, chunks:[{path,mtime,text}]} + vectors.npy
模型: BAAI/bge-small-zh-v1.5（fastembed，ONNX）
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import numpy as np

SCHEMA_VERSION = 1
SKIP_DIRS = {".git", ".venv", ".semantic"}


def chunk_text(text: str) -> list[str]:
    """按 \\section 切块；剔除注释/META/LaTeX 命令；超长再按句切。"""
    parts = re.split(r"\\section\*?\{", text)
    chunks = []
    for p in parts:
        p = "\n".join(l for l in p.splitlines() if not l.strip().startswith("%"))
        p = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", p)
        p = re.sub(r"[{}$&#^_~\\]", " ", p)
        p = re.sub(r"\s+", " ", p).strip()
        if len(p) < 10:
            continue
        if len(p) <= 600:
            chunks.append(p)
            continue
        for sent in re.split(r"(?<=[。！？；])\s*", p):
            sent = sent.strip()
            if len(sent) >= 10:
                chunks.append(sent[:600])
    return chunks


class SemanticService:
    DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"

    def __init__(self, data_dir: Path, model_name: str | None = None):
        self.data = Path(data_dir)
        self.cache = self.data / ".semantic"
        if model_name is None:
            try:
                from ..core import Config
                model_name = Config.load().semantic_model
            except Exception:  # noqa: BLE001
                model_name = self.DEFAULT_MODEL
        self.model_name = model_name or self.DEFAULT_MODEL

    def _scan(self) -> dict[str, float]:
        files = {}
        for root, dirs, fs in os.walk(self.data):
            dirs[:] = [d for d in dirs
                       if d not in SKIP_DIRS and not d.startswith((".", "_"))]
            for f in fs:
                if f in ("00-index.tex", "README.md"):
                    continue
                # 索引：笔记(tex/md) + 文档文本层(txt，如 pdfs/*.txt)
                if f.endswith((".tex", ".md", ".txt")):
                    p = Path(root) / f
                    files[str(p)] = p.stat().st_mtime
        return files

    def has_index(self) -> bool:
        return (self.cache / "chunks.json").exists() and (self.cache / "vectors.npy").exists()

    def build(self, full: bool = False) -> tuple[int, int]:
        """增量/全量建索引 → (总块数, 新嵌入块数)。"""
        from fastembed import TextEmbedding
        self.cache.mkdir(exist_ok=True)
        meta_p, vec_p = self.cache / "chunks.json", self.cache / "vectors.npy"
        old, vecs = [], np.zeros((0, 512), dtype=np.float32)
        if self.has_index() and not full:
            data = json.loads(meta_p.read_text(encoding="utf-8"))
            old = data.get("chunks", []) if data.get("schema_version", 1) == 1 else []
            vecs = np.load(vec_p)
            if vecs.shape[0] != len(old):
                old, vecs = [], np.zeros((0, 512), dtype=np.float32)
        files = self._scan()
        old_map = {c["path"]: c for c in old}
        changed = set()
        for p, m in files.items():
            if p in old_map and old_map[p]["mtime"] == m:
                continue
            try:
                text = Path(p).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if chunk_text(text):
                changed.add(p)
        if not changed:
            return len(old), 0
        model = TextEmbedding(model_name=self.model_name)
        new_c, new_v = [], []
        for p in sorted(changed):
            for ch in chunk_text(Path(p).read_text(encoding="utf-8", errors="ignore")):
                v = next(model.embed([ch]))
                new_c.append({"path": p, "mtime": files[p], "text": ch})
                new_v.append(np.asarray(v, dtype=np.float32))
        keep_idx = [i for i, c in enumerate(old) if c["path"] in files and c["path"] not in changed]
        final_c = [old[i] for i in keep_idx] + new_c
        final_v = np.vstack([vecs[keep_idx]] + new_v) if new_v else vecs[keep_idx]
        meta_p.write_text(json.dumps({"schema_version": SCHEMA_VERSION, "chunks": final_c},
                                     ensure_ascii=False), encoding="utf-8")
        np.save(vec_p, final_v)
        return len(final_c), len(new_c)

    def search(self, query: str, top: int = 5) -> list[tuple[dict, float]]:
        """语义检索 top-k → [(chunk, score)]；未建索引返回 []。"""
        if not self.has_index():
            return []
        from fastembed import TextEmbedding
        data = json.loads((self.cache / "chunks.json").read_text(encoding="utf-8"))
        chunks = data.get("chunks", []) if data.get("schema_version", 1) == 1 else []
        vecs = np.load(self.cache / "vectors.npy")
        model = TextEmbedding(model_name=self.model_name)
        qv = np.asarray(next(model.embed([query])), dtype=np.float32)
        sims = (vecs @ qv) / ((np.linalg.norm(vecs, axis=1) + 1e-9) * (np.linalg.norm(qv) + 1e-9))
        idxs = np.argsort(-sims)[:top]
        return [(chunks[i], float(sims[i])) for i in idxs]
