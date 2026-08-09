#!/usr/bin/env python3
"""语义索引构建器：把 TEX 笔记切片嵌入为向量，缓存到 .semantic/（增量更新）。

用法:
  embed.py                    # 增量（只嵌入新增/改动的文件）
  embed.py --full             # 全量重建
  embed.py --notes <路径>     # 指定库位置
首次运行需下载嵌入模型（BAAI/bge-small-zh-v1.5，~100MB），建议设置 HF_ENDPOINT=https://hf-mirror.com
"""
import argparse
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anote_config import data_dir as _cfg_data_dir
DEFAULT_NOTES = _cfg_data_dir()
SKIP_DIRS = {".git", ".venv", ".semantic"}


def chunk_text(text):
    r"""按 \section 切块；剔除注释/META/LaTeX 命令；超长块再按中文句读切。"""
    parts = re.split(r"\\section\*?\{", text)
    chunks = []
    for p in parts:
        # 剔除注释行（含 ==META==）与 LaTeX 命令
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


def scan(notes):
    files = {}
    for root, dirs, fs in os.walk(notes):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in fs:
            if (f.endswith(".tex") or f.endswith(".md")) and f not in ("00-index.tex", "README.md"):
                p = os.path.join(root, f)
                files[p] = os.path.getmtime(p)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notes", default=DEFAULT_NOTES)
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args()
    notes = os.path.expanduser(a.notes)
    cache = os.path.join(notes, ".semantic")
    os.makedirs(cache, exist_ok=True)
    meta, vecp = os.path.join(cache, "chunks.json"), os.path.join(cache, "vectors.npy")

    files = scan(notes)
    old = []
    vecs = np.zeros((0, 512), dtype=np.float32)
    if os.path.exists(meta) and os.path.exists(vecp) and not a.full:
        old = json.load(open(meta, encoding="utf-8"))
        if isinstance(old, dict):
            old = old.get("chunks", []) if old.get("schema_version", 1) == 1 else []
        vecs = np.load(vecp)
        if vecs.shape[0] != len(old):
            old, vecs = [], np.zeros((0, 512), dtype=np.float32)

    old_map = {c["path"]: c for c in old}
    changed = set()
    for p, m in files.items():
        if p in old_map and old_map[p]["mtime"] == m:
            continue
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:  # noqa: BLE001
            continue
        if chunk_text(text):
            changed.add(p)
    if not changed:
        print(f"✓ 语义索引已是最新（{len(old)} 块）")
        sys.exit(0)

    print(f"重嵌入 {len(changed)} 个文件（缓存 {len(old)} 块）...")
    from fastembed import TextEmbedding
    model = TextEmbedding(model_name="BAAI/bge-small-zh-v1.5")
    new_c, new_v = [], []
    for p in sorted(changed):
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:  # noqa: BLE001
            continue
        for ch in chunk_text(text):
            v = next(model.embed([ch]))
            new_c.append({"path": p, "mtime": files[p], "text": ch})
            new_v.append(np.asarray(v, dtype=np.float32))

    keep_idx = [i for i, c in enumerate(old) if c["path"] in files and c["path"] not in changed]
    final_c = [old[i] for i in keep_idx] + new_c
    final_v = np.vstack([vecs[keep_idx]] + new_v) if new_v else vecs[keep_idx]
    json.dump({"schema_version": 1, "chunks": final_c}, open(meta, "w", encoding="utf-8"), ensure_ascii=False)
    np.save(vecp, final_v)
    print(f"✓ 语义索引完成：{len(final_c)} 块，{final_v.shape} → {cache}")


if __name__ == "__main__":
    main()
