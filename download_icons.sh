#!/bin/bash
# LoL チャンピオンアイコン一括ダウンロードスクリプト
# 使い方: bash download_icons.sh

VERSION="14.10.1"
BASE="https://ddragon.leagueoflegends.com/cdn/${VERSION}/img/champion"
OUTDIR="./icons"

mkdir -p "$OUTDIR"

CHAMPS=(
  "Ahri" "Akali" "Akshan" "Anivia" "Annie" "AurelionSol"
  "Azir" "Brand" "Cassiopeia" "Corki" "Diana" "Ekko"
  "Fizz" "Galio" "Heimerdinger" "Irelia" "Jayce" "Katarina"
  "Leblanc" "Lissandra" "Lux" "Malzahar" "Naafiri" "Neeko"
  "Orianna" "Pantheon" "Qiyana" "Ryze" "Seraphine" "Smolder"
  "Sylas" "Syndra" "Taliyah" "Talon" "TwistedFate" "Veigar"
  "Vex" "Viktor" "Vladimir" "Xerath" "Yasuo" "Yone"
  "Zed" "Ziggs" "Zoe"
)

echo "ダウンロード開始 (バージョン: ${VERSION})"
echo "---"

for champ in "${CHAMPS[@]}"; do
  OUT="${OUTDIR}/${champ}.png"
  if [ -f "$OUT" ]; then
    echo "スキップ（既存）: ${champ}"
  else
    echo -n "ダウンロード中: ${champ}... "
    curl -s -o "$OUT" "${BASE}/${champ}.png"
    if [ $? -eq 0 ] && [ -s "$OUT" ]; then
      echo "OK"
    else
      echo "失敗"
      rm -f "$OUT"
    fi
  fi
done

echo "---"
echo "完了！ iconsフォルダを確認してください。"
