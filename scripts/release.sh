#!/usr/bin/env bash
# anote release <major|minor|patch> —— 发布门禁（测试→版本递增→tag）
set -e
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TYPE="${1:-minor}"
case "$TYPE" in major|minor|patch) ;; *) echo "用法: anote release <major|minor|patch>"; exit 1;; esac

echo "═══ ① 测试门禁 ═══"
bash "$PROJ/scripts/run-tests.sh" || { echo "✗ 门禁失败，中止发布"; exit 1; }

echo "═══ ② 版本递增 ═══"
cd "$PROJ"
V=$(cat VERSION)
MAJ=${V%%.*}; REST=${V#*.}; MIN=${REST%%.*}; PAT=${REST##*.}
case "$TYPE" in
  major) MAJ=$((MAJ+1)); MIN=0; PAT=0 ;;
  minor) MIN=$((MIN+1)); PAT=0 ;;
  patch) PAT=$((PAT+1)) ;;
esac
NEW="$MAJ.$MIN.$PAT"
echo "$NEW" > VERSION
echo "  $V → $NEW"

echo "═══ ③ 提交 + tag ═══"
git add VERSION && git commit -m "release: v$NEW" -q
git tag "v$NEW"
echo "✓ 已发布 v$NEW（git tag v$NEW；推送: git push --tags）"
