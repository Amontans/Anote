#!/usr/bin/env python3
"""anote zotero —— Zotero 接入（薄适配器；逻辑在 services/zotero.py）。"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.core import Config  # noqa: E402
from anote.services import zotero as z  # noqa: E402

SETUP_GUIDE = """Zotero + Better BibTeX 接入步骤：

1. 往 Zotero 添加文献——浏览器连接器抓取或手动添加。
2. 导出 refs.bib：右键 我的文库 → 导出 → 格式选 "Better BibTeX"（不要选 JSON！）
   → 勾选 "保持更新" → 保存到 {refs}
3. 验证：anote zotero bib 显示统计；anote bibcheck 校验引用链路
"""


def main() -> int:
    sub = sys.argv[1] if len(sys.argv) > 1 else "status"
    data = Config.load().data_dir
    refs = Path(data) / "refs.bib"
    if sub == "setup":
        print(SETUP_GUIDE.format(refs=refs))
        return 0
    if sub == "bib":
        entries = z.parse_bib(refs)
        print(f"refs.bib: {refs}\n条目总数: {len(entries)}")
        types = {}
        for t, _ in entries:
            types[t] = types.get(t, 0) + 1
        for t, n in sorted(types.items(), key=lambda x: -x[1]):
            print(f"  {t}: {n}")
        if not entries:
            print("\n提示: anote zotero setup 查看接入步骤")
        return 0
    items = z.library_count()
    bbt = z.bbt_installed()
    print(f"Zotero 数据目录: {z.ZOTERO_DATA}  {'✓' if z.ZOTERO_DATA.exists() else '✗'}  | 库条目: {items}")
    print(f"Better BibTeX 插件: {bbt or '✗ 未安装（anote zotero setup）'}")
    print(f"refs.bib: {refs}  {'✓' if refs.exists() else '✗（待导出）'}"
          + (f" | 条目 {len(z.parse_bib(refs))}" if refs.exists() else ""))
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
