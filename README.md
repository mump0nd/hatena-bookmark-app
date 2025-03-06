# はてなブックマーク ホットエントリー RSS ジェネレーター

このアプリケーションは、はてなブックマークのホットエントリーから指定したブックマーク数以上の記事を取得し、RSS形式で提供するFlaskアプリケーションです。

## 機能

- はてなブックマークAPIからホットエントリーを取得
- APIアクセスに失敗した場合はRSSフィードからデータを取得（フォールバック機能）
- 指定したブックマーク数（threshold）以上の記事をフィルタリング
- 記事の冒頭3段落を取得し、`<description>`に追加
- RSS 2.0形式でフィードを生成
- `<content:encoded>`にHTMLを含めたリッチなプレビューを追加
- 10分間のキャッシュ機能により、サーバーの負荷を軽減

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/mump0nd/hatena-bookmark-app.git
cd hatena_bookmark_app

# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 依存パッケージをインストール
pip install -r requirements.txt
```

## ローカルでの使い方

1. アプリケーションを起動します：

```bash
# 開発サーバーを起動
flask run
# または
python app.py
```

2. ブラウザで http://localhost:5001 にアクセスします
3. 以下のURLパターンでRSSフィードを取得できます：

```
http://localhost:5001/hotentry/all/feed?threshold=200
```

`threshold`パラメータに数値を指定することで、そのブックマーク数以上の記事のみをフィルタリングできます。

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
   - **Start Command**: `gunicorn app:app`

2. 「Create Web Service」ボタンをクリックします

### 4. アプリケーションにアクセス

デプロイが完了すると、以下のURLでアプリケーションにアクセスできます：
```
https://hatena-bookmark-app.onrender.com
```

RSSフィードは以下のURLで取得できます：
```
https://hatena-bookmark-app.onrender.com/hotentry/all/feed?threshold=200
```

## Renderの特徴

- **無料枠**: 月間750時間の実行時間（1つのサービスなら常時稼働可能）
- **スリープ機能**: 15分間アクセスがないとスリープ状態になり、無料枠を節約
- **API制限なし**: 外部APIへのアクセスが自由
- **GitHubとの連携**: コードを更新するとRenderも自動的に更新

## APIエンドポイント

### RSSフィードの取得

- `GET /hotentry/all/feed?threshold=XX`
- `threshold` に設定したブックマーク数以上のホットエントリーをRSSで返します
- デフォルト値は100です

## 出力例

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>Hatena Hotentry (Threshold: 200)</title>
        <link>https://example.com/hotentry/all/feed?threshold=200</link>
        <description>はてなブックマークの人気エントリー（200ブックマーク以上）</description>
        <language>ja</language>
        <lastBuildDate>Thu, 07 Mar 2024 15:00:00 GMT</lastBuildDate>
        <atom:link href="https://example.com/hotentry/all/feed?threshold=200" rel="self" type="application/rss+xml"/>

        <item>
            <title>「新しいAI技術が発表される」</title>
            <link>https://example.com/ai-news</link>
            <guid isPermaLink="true">https://example.com/ai-news</guid>
            <description>AI技術の進化が止まらない。最新の発表によると、新しいニューラルネットワークの手法が...専門家によると、この技術は...</description>
            <content:encoded><![CDATA[
                <p>AI技術の進化が止まらない。</p>
                <p>最新の発表によると、新しいニューラルネットワークの手法が...</p>
                <p>専門家によると、この技術は...</p>
            ]]></content:encoded>
            <pubDate>Thu, 07 Mar 2024 14:50:00 GMT</pubDate>
        </item>
    </channel>
</rss>
```

## トラブルシューティング

### Renderでのエラーログの確認

エラーが発生した場合は、Renderのダッシュボードで該当のWebサービスを選択し、「Logs」タブでエラーログを確認します。

### よくあるエラー

1. **ModuleNotFoundError**: 依存パッケージがインストールされていない場合に発生します。`requirements.txt`に必要なパッケージがすべて記載されていることを確認してください。

2. **Application Error**: アプリケーションの起動に失敗した場合に発生します。`Start Command`が正しく設定されているか確認してください。

3. **Build Failed**: ビルドプロセスに失敗した場合に発生します。`Build Command`が正しく設定されているか確認してください。

## ライセンス

MIT