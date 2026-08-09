#!/usr/bin/env bash
# 科研知识库一键自举：在新机器/损坏后重建全部基础设施（幂等，可重复运行）
# 用法: ./setup.sh [--full]
#   --full  连语义检索依赖一起安装（首次/换机器时用）
set -e
NOTES=~/Documents/Anote
PYV=$NOTES/.venv/bin/python

echo "═══ 科研知识库自举 v0.6.0 ═══"

# 1. 依赖检查（缺失仅提示，不中断）
echo "── [1/5] 基础依赖 ──"
for cmd in latexmk lualatex pdftotext rg git python3; do
  if command -v $cmd >/dev/null 2>&1; then echo "  ✓ $cmd"; else echo "  ✗ $cmd 缺失（Arch: sudo pacman -S texlive-latexmk poppler ripgrep git python）"; fi
done

# 2. Python venv + 语义检索依赖（仅 --full 或首次）
echo "── [2/5] Python 环境 ──"
if [ ! -x "$PYV" ] || [ "$1" == "--full" ]; then
  python3 -m venv .venv
  HF_ENDPOINT=https://hf-mirror.com "$PYV" -m pip install -q fastembed numpy
  echo "  ✓ venv + fastembed/numpy 就绪"
else
  echo "  ✓ venv 已存在（加 --full 重建）"
fi

# 3. git 钩子
echo "── [3/5] git 钩子 ──"
if [ -f .git/hooks/pre-commit ]; then
  echo "  ✓ pre-commit 已安装"
else
  echo "  ⚠️ 无 .git 仓库：先 git init 再重跑"
fi

# 4. 周回顾定时器（单元文件在项目 config/systemd/）
echo "── [4/6] 周回顾定时器 ──"
mkdir -p ~/.config/systemd/user
cp "$PROJ/config/systemd/notes-review.service" "$PROJ/config/systemd/notes-review.timer" ~/.config/systemd/user/ 2>/dev/null
systemctl --user daemon-reload 2>/dev/null
systemctl --user enable --now notes-review.timer >/dev/null 2>&1 && echo "  ✓ notes-review.timer 已启用"

# 5. anote 统一入口
echo "── [5/6] anote 命令 ──"
mkdir -p ~/.local/bin
ln -sf "$PROJ/anote" ~/.local/bin/anote
echo "  ✓ ~/.local/bin/anote（若 PATH 缺 ~/.local/bin 请自行添加）"

# 5. 索引 + 语义库 + 自检
echo "── [6/6] 构建索引 ──"
python3 scripts/index-gen.py >/dev/null && echo "  ✓ 分层索引"
if [ -x "$PYV" ]; then
  HF_ENDPOINT=https://hf-mirror.com "$PYV" scripts/embed.py || echo "  ⚠️ 语义索引失败（可用 notes index-semantic 重试）"
fi
python3 scripts/check.py 2>&1 | tail -1

echo "═══ 自举完成。远程备份: git remote add origin <gitee 地址> && ./manage.sh backup ═══"
