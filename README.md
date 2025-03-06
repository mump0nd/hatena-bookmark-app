# はてなブックマーク ホットエントリー RSS ジェネレーター

このアプリケーションは、はてなブックマークのホットエントリーから指定したブックマーク数以上の記事を取得し、RSS形式で提供するFlaskアプリケーションです。

## 機能

- はてなブックマークAPIからホットエントリーを取得
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

## PythonAnywhereでの公開手順

### 1. PythonAnywhereにアカウントを作成

1. [PythonAnywhere](https://www.pythonanywhere.com/)にアクセスし、アカウントを作成します（無料プランでOK）
2. ダッシュボードにログインします

### 2. コードをアップロード

#### 方法1: GitHubを使用する場合

1. GitHubにリポジトリを作成し、コードをプッシュします
2. PythonAnywhereのダッシュボードで「Consoles」タブを開き、「Bash」を選択します
3. 以下のコマンドを実行してリポジトリをクローンします：

```bash
git clone https://github.com/mump0nd/hatena-bookmark-app.git
```

#### 方法2: 直接ファイルをアップロードする場合

1. PythonAnywhereのダッシュボードで「Files」タブを開きます
2. 「mysite」ディレクトリに移動します（または新しいディレクトリを作成します）
3. 「Upload a file」ボタンを使用して、app.pyとrequirements.txtをアップロードします

### 3. 仮想環境を設定

1. PythonAnywhereのダッシュボードで「Consoles」タブを開き、「Bash」を選択します
2. 以下のコマンドを実行して仮想環境を作成し、依存パッケージをインストールします：

```bash
cd ~/hatena-bookmark-app  # または、アップロードしたディレクトリに移動
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Webアプリケーションを設定

1. PythonAnywhereのダッシュボードで「Web」タブを開きます
2. 「Add a new web app」ボタンをクリックします
3. ドメイン名を確認し（通常は「yourusername.pythonanywhere.com」）、「Next」をクリックします
4. 「Manual configuration」を選択し、Pythonのバージョンを選択して「Next」をクリックします
5. 以下の設定を行います：
   - **Code**: `/home/yourusername/hatena-bookmark-app`（または、アップロードしたディレクトリのパス）
   - **Working directory**: `/home/yourusername/hatena-bookmark-app`
   - **WSGI configuration file**: 自動的に作成されたファイルへのパスが表示されます

6. WSGIファイルを編集します：
   - 「WSGI configuration file」のリンクをクリックします
   - ファイルの内容を以下のように編集します：

```python
import sys
import os

# 仮想環境のパスを追加
path = '/home/yourusername/hatena-bookmark-app'
if path not in sys.path:
    sys.path.append(path)

# 仮想環境のサイトパッケージを追加
venv_path = os.path.join(path, 'venv')
site_packages = os.path.join(venv_path, 'lib', 'python3.9', 'site-packages')
if site_packages not in sys.path:
    sys.path.append(site_packages)

# アプリケーションをインポート
from app import application
```

7. 「Save」ボタンをクリックします
8. 「Web」タブに戻り、「Reload」ボタンをクリックしてアプリケーションを再起動します

### 5. アプリケーションにアクセス

1. ブラウザで `https://yourusername.pythonanywhere.com` にアクセスします
2. RSSフィードを取得するには、以下のURLにアクセスします：
   `https://yourusername.pythonanywhere.com/hotentry/all/feed?threshold=200`

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

### PythonAnywhereでのエラーログの確認

エラーが発生した場合は、PythonAnywhereのダッシュボードで「Web」タブを開き、「Error log」をクリックしてエラーログを確認します。

### よくあるエラー

1. **ModuleNotFoundError**: 依存パッケージがインストールされていない場合に発生します。仮想環境に必要なパッケージがすべてインストールされていることを確認してください。

2. **Permission Error**: ファイルのアクセス権限に問題がある場合に発生します。ファイルのパーミッションを確認してください。

3. **WSGI Import Error**: WSGIファイルの設定に問題がある場合に発生します。パスが正しく設定されていることを確認してください。

## ライセンス

MIT