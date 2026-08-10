#!/usr/bin/env python3
"""anote eval —— 检索质量评测（v1.9）：自命中率 + 人工查询集。

人工查询集: memory/eval-queries.md（每行: 查询 ===> 期望文件相对路径）
接口声明（契约）:
    输入: argv: [--k N]
    输出: stdout=评测报告；退出码 0/1
    副作用: 无
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.retrieval import RetrievalService  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    k = 3
    if "--k" in args:
        k = int(args[args.index("--k") + 1])
    data = Path(Config.load().data_dir)
    svc = RetrievalService(data)
    if not svc.sem.has_index():
        print("未建语义索引：anote index-semantic")
        return 1

    print(f"=== 检索质量评测（top-{k}）===\n")
    # ① 自命中
    r = svc.self_hit_eval(k=k)
    print(f"① 自命中率（标题查询命中自身）: {r['hit_rate']*100:.1f}%  ({r['hit_top'+str(k)]}/{r['sample']})")

    # ② 人工查询集
    eq = data / "memory" / "eval-queries.md"
    if eq.exists():
        hits, total = 0, 0
        for line in eq.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "===>" not in line:
                continue
            q, _, expect = line.partition("===>")
            q, expect = q.strip(), expect.strip()
            results = svc.retrieve(q, top=k)
            ok = any(expect in r[0].get("path", "") for r in results)
            hits += int(ok)
            total += 1
            print(f"  {'✓' if ok else '✗'} {q} → {expect}")
        if total:
            print(f"\n② 人工查询集命中率: {hits}/{total} = {hits/max(1,total)*100:.0f}%")
        else:
            print("\n② （eval-queries.md 为空，添加格式: 查询 ===> 文件路径）")
    else:
        print(f"\n② 未建人工查询集：创建 {eq}\n   每行: 查询 ===> 文件相对路径")
    print("\n评测完成。改进方向: 调 RetrievalService(vec_weight) 或补充 eval-queries.md。")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
