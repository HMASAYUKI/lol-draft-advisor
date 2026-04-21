# LoL ドラフトアドバイザー

LoLのドラフトピック中にリアルタイムでAIがアドバイスしてくれるWebアプリです。

## セットアップ手順

### 1. チャンピオンアイコンをダウンロード

```bash
bash download_icons.sh
```

`icons/` フォルダに全キャラのアイコン画像が保存されます。

### 2. GitHub にアップロード

```bash
git init
git add .
git commit -m "first commit"
git remote add origin https://github.com/あなたのユーザー名/lol-draft-advisor.git
git push -u origin main
```

### 3. GitHub Pages を有効化

1. リポジトリの **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** / **/ (root)**
4. **Save** をクリック

数分後に `https://ユーザー名.github.io/lol-draft-advisor/` でアクセス可能になります。

## 使い方

1. チャンピオンアイコンをタップして選択
2. **味方にピック** / **相手にピック** / **味方でBAN** / **相手でBAN** ボタンで追加
3. ピックが増えるたびにAIが自動でおすすめを更新
4. 全員確定したら詳細アドバイス（ビルド・立ち回り）が表示される

## ファイル構成

```
lol-draft-advisor/
├── index.html          # アプリ本体
├── download_icons.sh   # アイコン一括DLスクリプト
├── icons/              # チャンピオンアイコン画像
│   ├── Ahri.png
│   ├── Akali.png
│   └── ...
└── README.md
```
