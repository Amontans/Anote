#!/usr/bin/env bash
# 科研知识库一键自举：在新机器/损坏后重建全部基础设施（幂等，可重复运行）。
# 用法: ./setup.sh [--minimal|--full] [--skip-systemd]
set -e
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VER=$(cat "$PROJ/VERSION" 2>/dev/null || echo dev)

# 数据根：ANOTE_DATA > 旧配置指针 > 默认目录
if [ -n "${ANOTE_DATA:-}" ]; then
  DATA=$ANOTE_DATA
elif [ -f "$HOME/.config/anote/config" ]; then
  DATA=$(grep -E '^data_dir=' "$HOME/.config/anote/config" 2>/dev/null | head -1 | cut -d= -f2- | sed 's|^~|'"$HOME"'|')
fi
DATA=${DATA:-$HOME/Documents/Anote}
PYV="$DATA/.venv/bin/python"

echo "═══ Anote 科研知识库自举 v$VER ═══"
echo "项目: $PROJ"
echo "数据: $DATA"

# 0. 数据目录骨架（含配置；幂等）
echo "── [1/6] 数据目录 ──"
python3 "$PROJ/scripts/init_data.py"
if [ ! -d "$DATA/.git" ]; then
  git init -q "$DATA"
  echo "  ✓ git init 数据仓库"
else
  echo "  ✓ 数据仓库已存在"
fi

# 1. 依赖检查（缺失仅提示，不中断）
echo "── [2/6] 基础依赖 ──"
for cmd in latexmk lualatex pdftotext rg git python3; do
  if command -v $cmd >/dev/null 2>&1; then echo "  ✓ $cmd"; else echo "  ✗ $cmd 缺失（Arch: sudo pacman -S texlive-latexmk poppler ripgrep git python）"; fi
done

# 2. Python venv（--minimal=核心零 pip；默认=全量依赖）
echo "── [3/6] Python 环境 ──"
MODE="${1:-}"
if [ "$MODE" == "--minimal" ]; then
  echo "  ✓ minimal 模式：不装第三方依赖（语义/TUI/MCP 需时重跑 setup.sh --full）"
else
  if [ ! -x "$PYV" ] || [ "$MODE" == "--full" ]; then
    python3 -m venv "$DATA/.venv"
    HF_ENDPOINT=https://hf-mirror.com "$PYV" -m pip install -q -r "$PROJ/requirements.txt"
    echo "  ✓ venv + fastembed/numpy/textual/fastmcp 就绪"
  else
    echo "  ✓ venv 已存在（加 --full 重建）"
  fi
fi

# 3. 数据仓库 git 钩子（从项目模板安装，不写死项目路径）
echo "── [4/6] git 钩子 ──"
mkdir -p "$DATA/.git/hooks"
cp "$PROJ/config/git-hooks/pre-commit" "$DATA/.git/hooks/pre-commit"
cp "$PROJ/config/git-hooks/pre-push" "$DATA/.git/hooks/pre-push"
chmod +x "$DATA/.git/hooks/pre-commit" "$DATA/.git/hooks/pre-push"
echo "  ✓ pre-commit / pre-push 已安装"

# 4. systemd 定时器（可选）
echo "── [5/6] 定时任务 ──"
if [[ " $* " != *" --skip-systemd "* ]] && command -v systemctl >/dev/null 2>&1; then
  mkdir -p ~/.config/systemd/user
  for unit in notes-review notes-backup; do
    for ext in service timer; do
      sed "s|@@PROJECT@@|$PROJ|g" "$PROJ/config/systemd/$unit.$ext" > "$HOME/.config/systemd/user/$unit.$ext"
    done
  done
  systemctl --user daemon-reload 2>/dev/null || true
  systemctl --user enable --now notes-review.timer >/dev/null 2>&1 && echo "  ✓ notes-review.timer 已启用" || true
  systemctl --user enable --now notes-backup.timer >/dev/null 2>&1 && echo "  ✓ notes-backup.timer 已启用" || true
else
  echo "  ⚠️ 跳过 systemd（无 systemd 或用 --skip-systemd）。可手动 cron："
  echo "     每天 23:00: $PROJ/scripts/daily-backup.sh"
  echo "     每周一 09:00: $PROJ/scripts/weekly-review.sh"
fi

# 5. anote 统一入口
echo "── [6/6] anote 命令 ──"
mkdir -p ~/.local/bin
ln -sf "$PROJ/anote" ~/.local/bin/anote
echo "  ✓ ~/.local/bin/anote（若 PATH 缺 ~/.local/bin 请自行添加）"

# 6. 索引 + 语义库 + 自检
echo "── 构建索引 ──"
ANOTE_DATA="$DATA" python3 "$PROJ/scripts/index-gen.py" >/dev/null && echo "  ✓ 分层索引"
if [ -x "$PYV" ]; then
  ANOTE_DATA="$DATA" HF_ENDPOINT=${HF_ENDPOINT:-https://hf-mirror.com} "$PYV" "$PROJ/scripts/embed.py" || echo "  ⚠️ 语义索引失败（可用 anote index-semantic 重试）"
else
  echo "  ⚠️ minimal 模式：跳过语义索引"
fi
ANOTE_DATA="$DATA" python3 "$PROJ/scripts/check.py" 2>&1 | tail -1

echo "═══ 自举完成。远程备份: git -C $DATA remote add origin <gitee 地址> && anote backup ═══"
