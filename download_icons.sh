#!/bin/bash
# LoL チャンピオンアイコン一括ダウンロードスクリプト
# Data Dragon APIからチャンピオン一覧を取得して全アイコンをダウンロード
# 使い方: bash download_icons.sh

OUTDIR="./icons"
mkdir -p "$OUTDIR"

# 最新バージョンを取得
echo "最新バージョンを確認中..."
VERSION=$(curl -s "https://ddragon.leagueoflegends.com/api/versions.json" | python3 -c "import json,sys; print(json.load(sys.stdin)[0])")
echo "バージョン: ${VERSION}"

BASE="https://ddragon.leagueoflegends.com/cdn/${VERSION}/img/champion"

# APIからチャンピオン一覧を取得
echo "チャンピオン一覧を取得中..."
CHAMPS=$(curl -s "https://ddragon.leagueoflegends.com/cdn/${VERSION}/data/ja_JP/champion.json" \
  | python3 -c "import json,sys; data=json.load(sys.stdin); [print(k) for k in sorted(data['data'].keys())]")

TOTAL=$(echo "$CHAMPS" | wc -l | tr -d ' ')
echo "対象チャンピオン数: ${TOTAL}"
echo "---"

COUNT=0
SKIP=0
FAIL=0

while IFS= read -r champ; do
  OUT="${OUTDIR}/${champ}.png"
  if [ -f "$OUT" ] && [ -s "$OUT" ]; then
    SKIP=$((SKIP+1))
  else
    COUNT=$((COUNT+1))
    echo -n "ダウンロード中 [${COUNT}]: ${champ}... "
    curl -s -o "$OUT" "${BASE}/${champ}.png"
    if [ $? -eq 0 ] && [ -s "$OUT" ]; then
      echo "OK"
    else
      echo "失敗"
      rm -f "$OUT"
      FAIL=$((FAIL+1))
    fi
  fi
done <<< "$CHAMPS"

echo "---"
echo "ダウンロード: ${COUNT}件 / スキップ（既存）: ${SKIP}件 / 失敗: ${FAIL}件"
echo "完了！ iconsフォルダを確認してください。"
