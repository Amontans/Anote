#!/usr/bin/env bash
# 每日备份：数据仓库 commit + push（有远程时）
DATA=$(grep -E '^data_dir=' ~/.config/anote/config 2>/dev/null | head -1 | cut -d= -f2- | sed 's|^~|'"$HOME"'|')
DATA=${DATA:-~/Documents/Anote}
cd "$DATA" || exit 0
git add -A
git commit -m "auto-backup: $(date '+%F %H:%M')" 2>/dev/null || true
if git remote -v | grep -q push; then git push 2>/dev/null && echo "已推送"; else echo "无远程（跳过推送）"; fi
