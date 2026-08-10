#!/usr/bin/env bash
# 每日备份：数据仓库 commit + push（有远程时）
DATA=$(grep -E '^data_dir=' ~/.config/anote/config 2>/dev/null | head -1 | cut -d= -f2- | sed 's|^~|'"$HOME"'|')
DATA=${DATA:-~/Documents/Anote}
cd "$DATA" || exit 0
git add -A
git commit -m "auto-backup: $(date '+%F %H:%M')" 2>/dev/null || true
if git remote -v | grep -q push; then git push 2>/dev/null && echo "已推送"; else echo "无远程（跳过推送）"; fi

# 每周日：加密冷备
DOW=$(date +%u)
if [ "$DOW" = "7" ]; then
  [ -n "$ANOTE_BACKUP_KEY" ] && python3 ~/Projects/Anote/scripts/backup.py --encrypt --out ~/Documents/anote-backups 2>/dev/null || echo "（周日加密备份跳过：未设 ANOTE_BACKUP_KEY）"
fi
