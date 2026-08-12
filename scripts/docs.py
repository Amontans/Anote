#!/usr/bin/env python3
"""anote docs —— 文档管理（薄适配器；逻辑在 services/docs.py）。

用法: anote docs {list|add|update|progress|stats|import}
接口声明（契约）:
    输入: 见各子命令
    输出: stdout=表格/报告；退出码 0/1
    副作用: list/stats 只读；add/update/progress/import 写 docs/registry.md
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services.docs import DocService  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    sub = args[0] if args else "list"
    svc = DocService(Config.load().data_dir)

    def argval(flag, default=None):
        if flag in args:
            i = args.index(flag)
            return args[i + 1] if i + 1 < len(args) else default
        return default

    if sub == "list":
        entries = svc.filter(status=argval("--status", ""), tag=argval("--tag", ""),
                             doc_type=argval("--type", ""), sort=argval("--sort", "title"))
        print(f"{'状态':4} {'类型':6} {'标题':28} {'作者':14} {'年份':6} {'进度':6} 文件")
        for e in entries:
            print(f"{e.status:4} {e.doc_type:6} {e.title[:28]:28} {e.author[:14]:14} "
                  f"{e.year:6} {e.progress:6} {e.path}")
        print(f"\n共 {len(entries)} 条（--status/--tag/--type/--sort 过滤）")
        return 0
    if sub == "add":
        f = argval("--file")
        if not f:
            print("用法: anote docs add <文件> [--title --author --year --tags]")
            return 1
        meta = {k: argval(f"--{k}", "") for k in ("title", "author", "year", "tags")}
        meta = {k: v for k, v in meta.items() if v}
        ok, msg = svc.add(f, meta)
        print(msg)
        return 0 if ok else 1
    if sub == "update":
        f = argval("--file")
        if not f:
            print("用法: anote docs update <文件> [--status 📖 --progress 50% --tags ...]")
            return 1
        fields = {}
        for k in ("status", "progress", "tags", "note", "title", "author", "year", "doc_type"):
            v = argval(f"--{k}")
            if v:
                fields[k if k != "doc_type" else "doc_type"] = v
        svc.update(f, **fields)
        print(f"✓ 已更新: {f}")
        return 0
    if sub == "progress":
        f = argval("--file")
        pct = argval("--pct")
        if not f or not pct:
            print("用法: anote docs progress <文件> <百分比%>")
            return 1
        svc.progress(f, pct)
        print(f"✓ 进度 {f}: {pct}")
        return 0
    if sub == "stats":
        st = svc.stats()
        print(f"文档总数: {st['total']}")
        print("  状态: " + " ".join(f"{k}{st['status'].get(k,0)}" for k in ("📥", "📖", "✅", "🗄")))
        print("  类型: " + ", ".join(f"{k}={v}" for k, v in sorted(st['types'].items())))
        print(f"  未读占比: {st['unread_ratio']*100:.0f}%")
        return 0
    if sub == "import":
        d = argval("--dir", "")
        added, extracted = svc.import_dir(d)
        print(f"新登记 {len(added)} 个，提取文本 {len(extracted)} 个")
        for a in added[:10]:
            print(f"  ✓ {a}")
        return 0
    print("用法: anote docs {list|add|update|progress|stats|import}")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
