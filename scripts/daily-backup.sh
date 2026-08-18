#!/usr/bin/env bash
# 每日备份：数据仓库 commit + push（有远程时）；每周日可选加密冷备到 .anote/backups。
set -u
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -n "${ANOTE_DATA:-}" ]; then
  DATA=$ANOTE_DATA
elif [ -f "$HOME/.config/anote/config" ]; then
  DATA=$(grep -E '^data_dir=' "$HOME/.config/anote/config" 2>/dev/null | head -1 | cut -d= -f2- | sed 's|^~|'"$HOME"'|')
fi
DATA=${DATA:-$HOME/Documents/Anote}
cd "$DATA" || exit 0
git add -A
git commit -m "auto-backup: $(date '+%F %H:%M')" 2>/dev/null || true
if git remote -v | grep -q push; then git push 2>/dev/null && echo "已推送"; else echo "无远程（跳过推送）"; fi

# 每周日：加密冷备（配置了 ANOTE_BACKUP_KEY 时）
DOW=$(date +%u)
if [ "$DOW" = "7" ]; then
  if [ -n "${ANOTE_BACKUP_KEY:-}" ]; then
    ANOTE_DATA="$DATA" python3 "$PROJ/scripts/backup.py" --encrypt --out "$DATA/.anote/backups"
  else
    echo "（周日加密备份跳过：未设 ANOTE_BACKUP_KEY）"
  fi
fi
