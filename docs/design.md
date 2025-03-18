# はてなブックマーク ホットエントリー RSS ジェネレーター 設計書

## 1. 要件定義

### 1.1 目的

はてなブックマークのホットエントリーから指定したブックマーク数以上の記事を取得し、RSS形式で提供するFlaskアプリケーションを開発する。IFTTTのRSSトリガーと連携して、新しい人気記事の通知を自動化できるようにする。

### 1.2 機能要件

- はてなブックマークAPIからホットエントリーを取得する
- APIアクセスに失敗した場合はRSSフィードからデータを取得する（フォールバック機能）
- 指定したブックマーク数（threshold）以上の記事をフィルタリングする
- はてなブックマークの説明文を`<description>`に追加する
- RSS 2.0形式でフィードを生成する（IFTTTのRSSトリガーに対応）
- 常に最新のデータを取得する（キャッシュなし）
- UptimeRobotによる24時間監視でサーバーの常時稼働を維持する

### 1.3 非機能要件

- パフォーマンス: APIリクエストのタイムアウトは10秒以内
- 可用性: 24時間365日の稼働
- スケーラビリティ: 同時アクセス数の増加に対応
- セキュリティ: 適切なエラーハンドリングとログ出力
- 保守性: モジュール化された設計と適切なドキュメント

## 2. 全体設計

### 2.1 システム構成

```
クライアント（ブラウザ/IFTTT） <-> Render（Webサーバー） <-> はてなブックマークAPI
                                      |
                                      v
                               UptimeRobot（監視）
```

### 2.2 データフロー

1. クライアントがRSSフィードをリクエスト
2. アプリケーションがはてなブックマークAPIからデータを取得
3. 取得したデータをフィルタリングしてRSSフィードを生成
4. クライアントにRSSフィードを返す

## 3. 詳細設計

### 3.1 モジュール構成

- **app.py**: Flaskアプリケーションの定義とルーティング
- **api.py**: はてなブックマークAPIとの通信機能
- **feed.py**: RSSフィード生成機能
- **utils.py**: ユーティリティ関数

### 3.2 クラス設計

特に明示的なクラスは使用せず、関数ベースの設計を採用。

### 3.3 API仕様

#### 3.3.1 エンドポイント

- `GET /hotentry/all/feed?threshold=XX`: 指定したブックマーク数以上の記事をRSSで返す
- `GET /hotentry/all/feed/nocache?threshold=XX`: 上記と同じ（互換性のため）
- `GET /health`: ヘルスチェック用エンドポイント
- `GET /debug/ifttt`: IFTTTデバッグ用ページ
- `GET /`: ホームページ

#### 3.3.2 パラメータ

- `threshold`: ブックマーク数のしきい値（デフォルト: 100）

#### 3.3.3 レスポンス形式

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
        <ttl>10</ttl>

        <item>
            <title>記事タイトル</title>
            <link>https://example.com/article</link>
            <guid isPermaLink="false">https://example.com/article-200</guid>
            <description><![CDATA[記事の説明<br/><br/>ブックマーク数: 200]]></description>
            <pubDate>Thu, 07 Mar 2024 14:50:00 GMT</pubDate>
            <content:encoded><![CDATA[記事の説明<br/><br/>ブックマーク数: 200]]></content:encoded>
        </item>
    </channel>
</rss>
```

### 3.4 データ構造

エントリーの内部表現:

```python
{
    'title': '記事タイトル',
    'url': 'https://example.com/article',
    'description': '記事の説明',
    'count': 200,
    'date': '2023-01-01T00:00:00Z'
}
```

### 3.5 エラーハンドリング

- APIアクセスエラー: RSSフィードからのフォールバック
- その他のエラー: エラーメッセージを含むXMLレスポンスを返す

## 4. テスト計画

### 4.1 単体テスト

- **api.py**: APIからのデータ取得、RSSフィードからのデータ取得
- **feed.py**: RSSフィード生成、フィルタリング機能

### 4.2 統合テスト

- エンドポイントの動作確認
- エラーハンドリングの確認

### 4.3 エンドツーエンドテスト

- IFTTTとの連携確認
- UptimeRobotによる監視確認

## 5. デプロイ計画

### 5.1 開発環境

- ローカル開発: `flask run` または `python app.py`
- 依存パッケージ: requirements.txtに記載

### 5.2 本番環境（Render）

- Webサービスとしてデプロイ
- スタートコマンド: `gunicorn app:app --timeout 120 --workers 4`
- UptimeRobotによる5分間隔の監視

## 6. 運用計画

### 6.1 監視

- UptimeRobotによる定期的なヘルスチェック
- Renderのログ監視

### 6.2 バックアップ

- GitHubリポジトリによるコードのバックアップ

### 6.3 更新手順

1. GitHubリポジトリに変更をプッシュ
2. Renderが自動的にデプロイを実行