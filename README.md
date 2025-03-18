# はてなブックマーク ホットエントリー RSS ジェネレーター

このアプリケーションは、はてなブックマークのホットエントリーから指定したブックマーク数以上の記事を取得し、RSS形式で提供するFlaskアプリケーションです。IFTTTのRSSトリガーと連携して、新しい人気記事の通知を自動化できます。

## 機能

- はてなブックマークAPIからホットエントリーを取得
- APIアクセスに失敗した場合はRSSフィードからデータを取得（フォールバック機能）
- 指定したブックマーク数（threshold）以上の記事をフィルタリング
- はてなブックマークの説明文を`<description>`に追加
- RSS 2.0形式でフィードを生成（IFTTTのRSSトリガーに対応）
- 常に最新のデータを取得（キャッシュなし）
- UptimeRobotによる24時間監視でサーバーの常時稼働を維持

## IFTTTとの連携

### RSSトリガーの設定方法

1. IFTTTで新しいAppletを作成
2. 「If This」でトリガーとして「RSS Feed」を選択
3. 「New feed item」を選択
4. Feed URLに以下のURLを設定：
   ```
   https://hatena-bookmark-app.onrender.com/hotentry/all/feed?threshold=200
   ```
   - `threshold`パラメータで指定したブックマーク数以上の記事のみを取得
   - 常に最新のデータを取得
5. 「Then That」で任意のアクションを設定
   - Slackに通知
   - LINEに通知
   - Eメールで送信
   - など

### 注意点

- IFTTTは通常15-30分間隔でフィードをチェック
- 新しい記事は`pubDate`タグの日時を基準に判定

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/mump0nd/hatena-bookmark-app.git
cd hatena-bookmark-app

# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化
# Windows
# venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 依存パッケージをインストール
pip install -r requirements.txt

# 開発用パッケージをインストール（オプション）
pip install -r requirements-dev.txt
```

## ローカルでの使い方

1. アプリケーションを起動します：

```bash
# 開発サーバーを起動
flask run
# または
python -m src.hatena_bookmark.app
```

2. ブラウザで http://localhost:5001 にアクセスします
3. 以下のURLパターンでRSSフィードを取得できます：

```
# RSSフィードエンドポイント
http://localhost:5001/hotentry/all/feed?threshold=200
```

`threshold`パラメータに数値を指定することで、そのブックマーク数以上の記事のみをフィルタリングできます。

## プロジェクト構造

```
/
├── src/                       # ソースコードディレクトリ
│   └── hatena_bookmark/       # メインパッケージ
│       ├── __init__.py        # パッケージ初期化
│       ├── app.py             # アプリケーション定義
│       ├── api.py             # API関連の機能
│       ├── feed.py            # フィード生成機能
│       └── utils.py           # ユーティリティ関数
├── tests/                     # テストディレクトリ
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_feed.py
│   └── fixtures/              # テストデータ
│       └── popular_entries.xml
├── docs/                      # ドキュメントディレクトリ
│   ├── design.md              # 設計ドキュメント
│   └── render-cli.md          # Render CLIの使用ガイド
├── environments/              # 環境設定ディレクトリ
│   ├── dev/
│   │   └── .env.example       # 開発環境の環境変数例
│   ├── staging/
│   │   └── .env.example       # ステージング環境の環境変数例
│   └── prod/
│       └── .env.example       # 本番環境の環境変数例
├── infra/                     # インフラ設定ディレクトリ
│   └── Dockerfile             # Dockerファイル
├── .gitignore                 # Gitの除外設定
├── README.md                  # プロジェクト説明
├── requirements.txt           # 本番用依存パッケージ
├── requirements-dev.txt       # 開発用依存パッケージ
├── wsgi.py                    # WSGI設定
└── Procfile                   # Renderデプロイ設定
```

## テスト実行

```bash
# 全てのテストを実行
pytest

# カバレッジレポートを生成
pytest --cov=src

# 特定のテストを実行
pytest tests/test_api.py
```

## Renderでのデプロイ手順

### 1. Renderにアカウントを作成

1. [Render](https://render.com/)にアクセスし、アカウントを作成します
2. ダッシュボードにログインします

### 2. GitHubとの連携

1. GitHubにリポジトリを作成し、コードをプッシュします
2. Renderのダッシュボードで「New +」→「Web Service」を選択します
3. GitHubアカウントを連携し、リポジトリを選択します

### 3. Webサービスの設定

1. 以下の設定を行います：
   - **Name**: hatena-bookmark-app（または任意の名前）
   - **Region**: お近くのリージョン（例：Singapore）
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --timeout 120 --workers 4`

2. 「Create Web Service」ボタンをクリックします

### 4. UptimeRobotの設定

1. [UptimeRobot](https://uptimerobot.com/)にアカウントを作成
2. 「Add New Monitor」をクリック
3. 以下の設定を行います：
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Hatena Bookmark App
   - **URL**: https://hatena-bookmark-app.onrender.com/health
   - **Monitoring Interval**: 5 minutes

これにより、Renderの無料プランでもサーバーが停止せず、IFTTTのトリガーが正常に機能します。

## APIエンドポイント

### RSSフィードの取得

1. **RSSフィードエンドポイント**
   - `GET /hotentry/all/feed?threshold=XX`
   - 常に最新データを取得
   - ブラウザでの閲覧やIFTTTのRSSトリガーに最適

2. **ヘルスチェックエンドポイント**
   - `GET /health`
   - UptimeRobotによる監視用
   - サーバーの稼働状態を確認

- `threshold` に設定したブックマーク数以上のホットエントリーをRSSで返します
- デフォルト値は100です

## トラブルシューティング

### Renderでのエラーログの確認

#### Webダッシュボードでの確認

エラーが発生した場合は、Renderのダッシュボードで該当のWebサービスを選択し、「Logs」タブでエラーログを確認します。

#### Render CLIを使用したログの確認

Render CLIを使用すると、コマンドラインからログを確認できます。詳細な使用方法は [docs/render-cli.md](docs/render-cli.md) を参照してください。

基本的な使用方法：

```bash
# Render CLIのインストール
npm install -g @render/cli

# ログイン
render login

# リアルタイムログの表示
render logs hatena-bookmark-app

# 過去1時間のログを表示
render logs hatena-bookmark-app --since 1h

# エラーでフィルタリング
render logs hatena-bookmark-app --filter "error"
```

### よくあるエラー

1. **ModuleNotFoundError**: 依存パッケージがインストールされていない場合に発生します。`requirements.txt`に必要なパッケージがすべて記載されていることを確認してください。

2. **Application Error**: アプリケーションの起動に失敗した場合に発生します。`Start Command`が正しく設定されているか確認してください。

3. **Build Failed**: ビルドプロセスに失敗した場合に発生します。`Build Command`が正しく設定されているか確認してください。

### IFTTTのトラブルシューティング

1. **トリガーが発動しない**
   - RSSフィードのURLが正しいか確認
   - IFTTTの更新間隔（15-30分）を考慮
   - UptimeRobotの監視が正常に機能しているか確認

2. **トリガーがタイムアウトする**
   - UptimeRobotの監視が正常に機能しているか確認
   - Renderのダッシュボードでサーバーの状態を確認
   - 必要に応じてUptimeRobotの監視間隔を調整

3. **重複した通知**
   - `guid`タグが正しく設定されているか確認
   - IFTTTのAppletの設定を確認

## 開発者向け情報

### コーディング規約

- PEP8に準拠したコードスタイル
- Googleスタイルのドキュメント文字列
- ruffによるリンティングとフォーマット
- mypyによる型チェック

### 貢献方法

1. リポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Requestを作成

## ライセンス

MIT