#!/usr/bin/env bash
set -o pipefail
# anote test —— 一键测试门禁（单测 + TUI 双测试 + 自检）
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -n "${ANOTE_DATA:-}" ]; then
  DATA=$ANOTE_DATA
elif [ -f "$HOME/.config/anote/config" ]; then
  DATA=$(grep -E '^data_dir=' "$HOME/.config/anote/config" 2>/dev/null | head -1 | cut -d= -f2- | sed 's|^~|'"$HOME"'|')
fi
DATA=${DATA:-$HOME/Documents/Anote}
PYV="$DATA/.venv/bin/python"; [ -x "$PYV" ] || PYV=python3
fail=0
echo "═══ ① 单元测试 ═══"; (cd "$PROJ" && "$PYV" -m unittest discover -s tests 2>&1 | tail -1); [ "${PIPESTATUS[0]}" = "0" ] || fail=1
echo "═══ ② TUI 冒烟 ═══"; (cd "$PROJ" && "$PYV" -m tui.test_smoke 2>&1 | tail -1) || fail=1
echo "═══ ③ TUI 动作 ═══"; (cd "$PROJ" && "$PYV" -m tui.test_actions 2>&1 | tail -1) || fail=1
echo "═══ ④ 数据自检 ═══"; ANOTE_DATA="$DATA" python3 "$PROJ/scripts/check.py" --strict 2>&1 | tail -1 || fail=1
[ $fail -eq 0 ] && echo "✅ 门禁通过" || { echo "❌ 门禁失败"; exit 1; }
