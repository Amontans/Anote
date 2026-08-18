#!/usr/bin/env bash
# 每周回顾自动化：生成草稿 + 自动提交数据仓库（systemd 定时器调用）。
set -u
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -n "${ANOTE_DATA:-}" ]; then
  DATA=$ANOTE_DATA
elif [ -f "$HOME/.config/anote/config" ]; then
  DATA=$(grep -E '^data_dir=' "$HOME/.config/anote/config" 2>/dev/null | head -1 | cut -d= -f2- | sed 's|^~|'"$HOME"'|')
fi
DATA=${DATA:-$HOME/Documents/Anote}
ANOTE_DATA="$DATA" python3 "$PROJ/scripts/review.py" --days 7 || true
cd "$DATA" || exit 0
git add -A
git commit -m "weekly review draft: $(date +%F)" 2>/dev/null || echo "无变更"
