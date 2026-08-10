#!/usr/bin/env python3
"""anote zotero —— Zotero 文献库接入（v1.3）。

接口声明（契约）:
    输入: argv: status | bib | setup
    输出: stdout=状态/统计/指引；退出码 0/1
    副作用: 无（只读）
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402

ZOTERO_DIR = Path("~/.zotero/zotero").expanduser()

SETUP_GUIDE = """Zotero + Better BibTeX 接入步骤（一次性）：

1. 安装 Better BibTeX 插件：
   - 已下载: ~/Downloads/zotero-better-bibtex-9.0.55.xpi
   - Zotero → 工具 → 插件 → ⚙️ → 从文件安装插件… → 选择该 xpi → 重启 Zotero

2. 自动导出 refs.bib（二选一）：
   A. 整库导出：右键 我的文库 → 导出 → 格式选 Better BibTeX → 勾选"保持更新"（自动导出到 ~/Documents/Anote/refs.bib）
   B. 或文件夹导出：对特定收藏夹重复上述操作
   （导出时勾选"导出文件到库"可把 PDF 一并管理）

3. 验证：运行  anote zotero bib  应显示条目统计；anote bibcheck 校验引用链路
"""

BIB_ENTRY = re.compile(r"@(\w+)\{([^,]+),", re.M)


def parse_bib(path: Path) -> list[tuple[str, str]]:
    """解析 refs.bib → [(type, key)]。"""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [(m.group(1), m.group(2).strip()) for m in BIB_ENTRY.finditer(text)]


def main() -> int:
    args = sys.argv[1:]
    sub = args[0] if args else "status"
    data = Config.load().data_dir
    refs = Path(data) / "refs.bib"

    if sub == "setup":
        print(SETUP_GUIDE)
        return 0

    if sub == "bib":
        entries = parse_bib(refs)
        print(f"refs.bib: {refs}")
        print(f"条目总数: {len(entries)}")
        types = {}
        for t, _ in entries:
            types[t] = types.get(t, 0) + 1
        for t, n in sorted(types.items(), key=lambda x: -x[1]):
            print(f"  {t}: {n}")
        recent = entries[-5:]
        if recent:
            print("最近条目:")
            for _, k in recent:
                print(f"  • {k}")
        if not entries:
            print("\n提示: 运行 anote zotero setup 查看接入步骤")
        return 0

    # status
    print(f"Zotero 数据目录: {ZOTERO_DIR}  {'✓' if ZOTERO_DIR.exists() else '✗（首次启动 Zotero 后生成）'}")
    print(f"refs.bib: {refs}  {'✓' if refs.exists() else '✗（待 Better BibTeX 导出）'}")
    if refs.exists():
        print(f"refs.bib 条目: {len(parse_bib(refs))}")
    print("\nanote zotero setup  → 查看接入步骤")
    print("anote zotero bib   → 查看 refs.bib 统计")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
