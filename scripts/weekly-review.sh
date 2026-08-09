#!/usr/bin/env bash
# 每周回顾自动化：生成草稿 + 自动提交数据仓库（systemd 定时器调用）
set -e
DATA=$(grep -E '^data_dir=' ~/.config/anote/config 2>/dev/null | head -1 | cut -d= -f2- | sed 's|^~|'"$HOME"'|')
DATA=${DATA:-~/Documents/Anote}

python3 ~/Projects/Anote/scripts/review.py --days 7 || true

cd "$DATA"
git add -A
git commit -m "weekly review draft: $(date +%F)" 2>/dev/null || echo "无变更"
