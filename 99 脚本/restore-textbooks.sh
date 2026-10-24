#!/bin/bash
# 从 GitHub Release 拉回教材 PDF 到本仓库的正确位置
#
#   bash "99 脚本/restore-textbooks.sh"           # 缺什么补什么
#   bash "99 脚本/restore-textbooks.sh" --force    # 全部重下
#
# 仓库为了体积不含 PDF（单本 200MB+ 超 GitHub 单文件 100MB 上限），
# 教材与思维导图放在 Release: textbooks-2027

set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

OWNER="2486809961-alt"
REPO="wangdao-408"
RELEASE="textbooks-2027"
MANIFEST="99 脚本/textbooks-manifest.json"
FORCE="${1:-}"

[ -f "$MANIFEST" ] || { echo "缺少 $MANIFEST"; exit 1; }

BASE="https://github.com/${OWNER}/${REPO}/releases/download/${RELEASE}"
TMP=".textbooks-download"
mkdir -p "$TMP"

bytes_of() { wc -c < "$1" | tr -d ' '; }
sha_of()   { shasum -a 256 "$1" | cut -d' ' -f1; }

python3 - "$MANIFEST" <<'PY' > "$TMP/plan.tsv"
import json, sys
m = json.load(open(sys.argv[1]))
for f in m["files"]:
    print("\t".join([f["asset"], f["path"], str(f["bytes"]), f["sha256"]]))
PY

ok=0; skip=0; fail=0
while IFS=$'\t' read -r asset path size sha; do
  if [ -f "$path" ] && [ "$FORCE" != "--force" ]; then
    if [ "$(bytes_of "$path")" = "$size" ] && [ "$(sha_of "$path")" = "$sha" ]; then
      echo "✓ 已存在 ${path}"; skip=$((skip+1)); continue
    fi
    echo "≠ 尺寸或校验不符，重下：${path}"
  fi
  mkdir -p "$(dirname "$path")"
  echo "↓ ${asset} → ${path}"
  if curl -fL --retry 5 --retry-delay 3 --retry-all-errors -C - \
        -o "$TMP/$asset" "${BASE}/${asset}"; then
    if [ "$(sha_of "$TMP/$asset")" = "$sha" ]; then
      mv -f "$TMP/$asset" "$path"; echo "  ✓ sha256 校验通过"; ok=$((ok+1))
    else
      echo "  ✗ sha256 不符，丢弃"; rm -f "$TMP/$asset"; fail=$((fail+1))
    fi
  else
    echo "  ✗ 下载失败（可能是网络，重跑本脚本会续传）"; fail=$((fail+1))
  fi
done < "$TMP/plan.tsv"

rmdir "$TMP" 2>/dev/null || true
echo
echo "完成：新增 ${ok} / 跳过 ${skip} / 失败 ${fail}"
echo "回仓库根目录用 Obsidian 打开，教材链接即可点开。"

# 可选：同步到坚果云时把 PDF 排除，避免每次传输 1GB
# 在 Nutstore Sync 过滤规则里加 *.pdf 即可（插件设置 → 过滤）。