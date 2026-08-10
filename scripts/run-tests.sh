#!/usr/bin/env bash
# anote test —— 一键测试门禁（单测 + TUI 双测试 + 自检）
DATA=$(grep -E '^data_dir=' ~/.config/anote/config 2>/dev/null | head -1 | cut -d= -f2- | sed 's|^~|'"$HOME"'|')
DATA=${DATA:-~/Documents/Anote}
PYV="$DATA/.venv/bin/python"; [ -x "$PYV" ] || PYV=python3
fail=0
echo "═══ ① 单元测试 ═══"; $PYV -m unittest discover -s ~/Projects/Anote/tests 2>&1 | tail -2 | head -1 || fail=1
echo "═══ ② TUI 冒烟 ═══"; (cd ~/Projects/Anote && $PYV -m tui.test_smoke 2>&1 | tail -1) || fail=1
echo "═══ ③ TUI 动作 ═══"; (cd ~/Projects/Anote && $PYV -m tui.test_actions 2>&1 | tail -1) || fail=1
echo "═══ ④ 数据自检 ═══"; python3 ~/Projects/Anote/scripts/check.py 2>&1 | tail -1 || fail=1
[ $fail -eq 0 ] && echo "✅ 门禁通过" || { echo "❌ 门禁失败"; exit 1; }
