#!/usr/bin/env bash
# 科研知识库一键管理命令
# 用法: notes <命令>
#   index           重建分层索引
#   index-semantic  重建/增量更新语义索引（B 方案）
#   check           一致性自检（6 项）
#   review          生成周回顾草稿（--days 30 为月度）
#   ask             关键词检索问答: notes ask "词" | notes ask --smart "问题" | notes ask --semantic "问题"
#   new             新建笔记: notes new 数学/代数 "标题"（自动 META + 模板）
#   project         新建项目: notes project "项目名" "一句话目标"
#   commit          提交: notes commit "说明"
#   backup          提交并推送远程
#   all             全流程: index + check
set -e
PROJ=~/Projects/Anote
SKILL=$PROJ/scripts
NOTES=~/Documents/Anote
PYV=$NOTES/.venv/bin/python

case "$1" in
  index)
    python3 $SKILL/index-gen.py ;;
  index-semantic)
    shift; HF_ENDPOINT=https://hf-mirror.com $PYV $SKILL/embed.py "$@" ;;
  check)
    python3 $SKILL/check.py ;;
  review)
    shift; python3 $SKILL/review.py "$@" ;;
  ask)
    shift
    if [[ "$*" == *"--semantic"* ]]; then $PYV $SKILL/ask.py "$@"
    else python3 $SKILL/ask.py "$@"; fi ;;
  new)
    # notes new <学科/分支...> <标题>
    dir="$2"; title="$3"
    if [ -z "$dir" ] || [ -z "$title" ]; then
      echo "用法: notes new <学科/分支...> <标题>"; exit 1
    fi
    path="$NOTES/src/$dir"; mkdir -p "$path"
    f="$path/$(date +%F)_$(echo "$title" | tr ' ' '_').tex"
    cat > "$f" <<EOF
% ==META== 学科: ${dir%/*} | 分支: ${dir##*/} | 标签: | 日期: $(date +%F) | 来源: 教材
\documentclass[11pt]{ctexart}
\usepackage[margin=2.5cm]{geometry}
\usepackage{paralist,amsmath,amssymb}
\title{$title}
\date{\today}
\begin{document}
\maketitle
\section{主题}
\begin{compactitem}
  \item 
\end{compactitem}
\end{document}
EOF
    echo "✓ 已创建: $f"
    echo "（提交时 pre-commit hook 会自动更新索引）" ;;
  project)
    name="$2"; goal="$3"
    if [ -z "$name" ]; then
      echo "用法: notes project <项目名> <一句话目标>"; exit 1
    fi
    d="$NOTES/projects/$name"; mkdir -p "$d"
    cp "$NOTES/projects/_template/plan.tex" "$d/plan.tex"
    cp "$NOTES/projects/_template/log.tex" "$d/log.tex"
    if [ -n "$goal" ]; then
      sed -i "s/一句话：这个项目要回答什么问题 \/ 产出什么/$goal/" "$d/plan.tex" 2>/dev/null || true
    fi
    echo "✓ 项目已创建: $d（plan/log 就位，可让我起草细节）" ;;
  book)
    # notes book <书名> [作者]
    name="$2"; author="${3:-作者}"
    if [ -z "$name" ]; then
      echo "用法: notes book <书名> [作者]"; exit 1
    fi
    d="$NOTES/books/$name"; mkdir -p "$d/chapters" "$d/figures"
    cp "$NOTES/books/_template/main.tex" "$d/main.tex"
    cp "$NOTES/books/_template/chapters/ch01.tex" "$d/chapters/ch01.tex"
    cp "$NOTES/books/_template/refs.bib" "$d/refs.bib"
    cp "$NOTES/books/_template/latexmkrc" "$d/latexmkrc"
    sed -i "s/书名（在 manage.sh book 生成时填入）/$name/; s/^\\author{.*}$/\\author{$author}/" "$d/main.tex" 2>/dev/null
    echo "✓ 教科书已创建: $d（编译: cd $d && latexmk -lualatex main.tex）" ;;
  book-build)
    name="$2"
    [ -z "$name" ] && { echo "用法: notes book-build <书名>"; exit 1; }
    cd "$NOTES/books/$name" && latexmk -lualatex -interaction=nonstopmode main.tex 2>&1 | tail -3 ;;
  chapter)
    # notes chapter <书名> <章节标题>
    book="$2"; title="$3"
    if [ -z "$book" ] || [ -z "$title" ]; then
      echo "用法: notes chapter <书名> <章节标题>"; exit 1
    fi
    d="$NOTES/books/$book/chapters"
    n=$(ls "$d" 2>/dev/null | wc -l); n=$((n+1))
    f="$d/ch$(printf %02d $n).tex"
    printf '%%%% ===== 第 %d 章 =====\n\\chapter{%s}\n\\label{ch:auto%d}\n\n正文从这里写起。\n' "$n" "$title" "$n" > "$f"
    # 在 main.tex 的 \include{chapters/ch01} 后追加
    sed -i "s|\\include{chapters/ch01}|\\include{chapters/ch01}\n\\include{chapters/ch$(printf %02d $n)}|" "$NOTES/books/$book/main.tex" 2>/dev/null || true
    echo "✓ 章节已创建: $f（已加入 main.tex）" ;;
  commit)
    cd "$NOTES" && git add -A && git commit -m "${2:-update}" ;;
  backup)
    cd "$NOTES" && git add -A && git commit -m "backup: $(date '+%Y-%m-%d %H:%M')" || echo "无新变更"
    if git remote -v | grep -q push; then git push && echo "✅ 已推送远程"
    else echo "⚠️ 未配置远程: git remote add origin <gitee 地址>"; fi ;;
  all)
    python3 $SKILL/index-gen.py && python3 $SKILL/check.py ;;
  *)
    echo "用法: notes {index|index-semantic|check|review|ask|new|project|book|book-build|chapter|commit|backup|all}" ;;
esac
