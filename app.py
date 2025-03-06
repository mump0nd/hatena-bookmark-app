from flask import Flask, request, Response, url_for
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time
from dateutil import parser
import re
from functools import wraps
import threading
import html
import os
import random
import email.utils
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

app = Flask(__name__)

# グローバルなデータストア
global_store = {
    'latest_entries': None,
    'last_update': None
}
store_lock = threading.Lock()

# スケジューラーの初期化
scheduler = BackgroundScheduler()

# User-Agentのリスト
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'
]

# リクエストセッション
session = requests.Session()
session.headers.update({
    'Accept': 'application/json, text/xml',
    'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
})

def format_rfc822_date(date_str=None):
    """日付文字列をRFC822形式に変換する"""
    if date_str:
        try:
            dt = parser.parse(date_str)
        except:
            dt = datetime.now()
    else:
        dt = datetime.now()
    return email.utils.format_datetime(dt)

def fetch_hatena_hotentries():
    """はてなブックマークのホットエントリーを取得する"""
    try:
        # APIからデータを取得
        url = "https://b.hatena.ne.jp/api/ipad.hotentry?mode=general"
        session.headers['User-Agent'] = random.choice(USER_AGENTS)
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        app.logger.error(f"APIからのデータ取得に失敗しました: {str(e)}")
        # 失敗した場合はRSSフィードから取得
        return fetch_hatena_hotentries_from_rss()

def fetch_hatena_hotentries_from_rss():
    """はてなブックマークのホットエントリーをRSSフィードから取得する"""
    url = "https://b.hatena.ne.jp/hotentry.rss"
    session.headers['User-Agent'] = random.choice(USER_AGENTS)
    response = session.get(url, timeout=10)
    response.raise_for_status()
    
    # RSSフィードをパース
    entries = []
    root = ET.fromstring(response.content)
    
    # 名前空間を定義
    namespaces = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'rss': 'http://purl.org/rss/1.0/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'hatena': 'http://www.hatena.ne.jp/info/xmlns#'
    }
    
    # RSSアイテムを取得
    items = root.findall('.//rss:item', namespaces)
    
    for item in items:
        title = item.find('rss:title', namespaces).text
        link = item.find('rss:link', namespaces).text
        description = item.find('rss:description', namespaces).text
        date_str = item.find('dc:date', namespaces).text if item.find('dc:date', namespaces) is not None else None
        
        # はてなブックマーク数を取得
        hatena_count = item.find('.//hatena:bookmarkcount', namespaces)
        count = int(hatena_count.text) if hatena_count is not None else 0
        
        entries.append({
            'title': title,
            'url': link,
            'description': description,
            'count': count,
            'date': date_str
        })
    
    return entries

def update_global_store():
    """グローバルストアのデータを更新する"""
    try:
        entries = fetch_hatena_hotentries()
        with store_lock:
            global_store['latest_entries'] = entries
            global_store['last_update'] = datetime.now()
        app.logger.info("グローバルストアのデータを更新しました")
    except Exception as e:
        app.logger.error(f"グローバルストアの更新に失敗しました: {str(e)}")

def generate_rss_feed(entries, threshold):
    """エントリーからRSSフィードを生成する（文字列操作でXMLを生成）"""
    current_time = format_rfc822_date()
    host_url = request.host_url.rstrip('/')
    
    # XMLヘッダーとRSS開始タグ
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:atom="http://www.w3.org/2005/Atom">\n'
    xml += '  <channel>\n'
    
    # チャンネル情報
    xml += f'    <title>Hatena Hotentry (Threshold: {threshold})</title>\n'
    xml += f'    <link>{html.escape(host_url)}</link>\n'
    xml += f'    <description>はてなブックマークの人気エントリー（{threshold}ブックマーク以上）</description>\n'
    xml += '    <language>ja</language>\n'
    xml += f'    <lastBuildDate>{current_time}</lastBuildDate>\n'
    xml += f'    <atom:link href="{html.escape(request.url)}" rel="self" type="application/rss+xml"/>\n'
    xml += '    <generator>Hatena Bookmark RSS Generator</generator>\n'
    xml += '    <ttl>5</ttl>\n'  # TTLを5分に設定
    
    # 各エントリー
    for entry in entries:
        # エントリーのIDを生成（URLとブックマーク数からハッシュ値を生成）
        entry_id = f"{entry.get('url', '')}-{entry.get('count', 0)}"
        
        # 日付をRFC822形式に変換
        pub_date = format_rfc822_date(entry.get('date'))
        
        # 説明を取得（HTMLエスケープ処理）
        description = html.escape(entry.get("description", "説明なし"))
        description += f"<br/><br/>ブックマーク数: {entry.get('count', 0)}"
        
        # アイテムを生成
        xml += '    <item>\n'
        xml += f'      <title>{html.escape(entry.get("title", "無題"))}</title>\n'
        xml += f'      <link>{html.escape(entry.get("url", ""))}</link>\n'
        xml += f'      <guid isPermaLink="false">{html.escape(entry_id)}</guid>\n'
        xml += f'      <description><![CDATA[{description}]]></description>\n'
        xml += f'      <pubDate>{pub_date}</pubDate>\n'
        xml += f'      <content:encoded><![CDATA[{description}]]></content:encoded>\n'
        xml += '    </item>\n'
    
    # 終了タグ
    xml += '  </channel>\n'
    xml += '</rss>'
    
    return xml

def get_hotentry_feed_internal(threshold=100, use_cache=True):
    """ホットエントリーのRSSフィードを生成する内部関数"""
    if use_cache:
        with store_lock:
            if global_store['latest_entries'] is not None:
                entries = global_store['latest_entries']
            else:
                entries = fetch_hatena_hotentries()
                global_store['latest_entries'] = entries
                global_store['last_update'] = datetime.now()
    else:
        entries = fetch_hatena_hotentries()
    
    # しきい値以上のブックマーク数を持つエントリーをフィルタリング
    filtered_entries = []
    
    for entry in entries:
        # ブックマーク数を取得
        bookmark_count = entry.get('count', 0)
        
        if bookmark_count >= threshold:
            filtered_entries.append(entry)
    
    # RSSフィードを生成
    rss_feed = generate_rss_feed(filtered_entries, threshold)
    
    # XMLレスポンスを返す
    return Response(rss_feed, mimetype='application/xml')

@app.route('/hotentry/all/feed')
def get_hotentry_feed():
    """ホットエントリーのRSSフィードを返す（キャッシュあり）"""
    # クエリパラメータからしきい値を取得（デフォルトは100）
    threshold = request.args.get('threshold', '100')
    try:
        threshold = int(threshold)
    except ValueError:
        threshold = 100
    
    return get_hotentry_feed_internal(threshold, use_cache=True)

@app.route('/hotentry/all/feed/nocache')
def get_hotentry_feed_nocache():
    """ホットエントリーのRSSフィードを返す（キャッシュなし、IFTTT用）"""
    # クエリパラメータからしきい値を取得（デフォルトは100）
    threshold = request.args.get('threshold', '100')
    try:
        threshold = int(threshold)
    except ValueError:
        threshold = 100
    
    return get_hotentry_feed_internal(threshold, use_cache=False)

@app.route('/debug/ifttt')
def debug_ifttt():
    """IFTTTデバッグ用のエンドポイント"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IFTTT RSSトリガーデバッグ</title>
        <meta charset="utf-8">
        <style>
            body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            pre { background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
            .item { border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>IFTTT RSSトリガーデバッグ</h1>
        <p>このページは、IFTTTのRSSトリガーで問題が発生した場合のデバッグに使用します。</p>
        
        <h2>IFTTTでの設定方法</h2>
        <ol>
            <li>IFTTTで「RSS Feed」トリガーを選択</li>
            <li>以下のURLを入力: <code>""" + request.host_url + """hotentry/all/feed/nocache?threshold=200</code></li>
            <li>「New feed item」を選択</li>
            <li>任意のアクションを設定（例: Lineに通知）</li>
        </ol>
        
        <h2>トラブルシューティング</h2>
        <ol>
            <li>キャッシュなしのエンドポイント (<code>/nocache</code>) を使用しているか確認</li>
            <li>URLが正しいか確認（特に末尾のスラッシュ）</li>
            <li>しきい値が適切か確認（あまり高いと記事が少なくなる）</li>
            <li>IFTTTの「Check now」ボタンを押して手動で確認</li>
        </ol>
        
        <h2>現在の最新エントリー</h2>
        <div id="entries">読み込み中...</div>
        
        <script>
            fetch('/hotentry/all/feed/nocache?threshold=200')
                .then(response => response.text())
                .then(text => {
                    const parser = new DOMParser();
                    const xmlDoc = parser.parseFromString(text, "text/xml");
                    const items = xmlDoc.getElementsByTagName("item");
                    let html = '';
                    
                    if (items.length === 0) {
                        html = '<p>エントリーがありません。しきい値を下げてみてください。</p>';
                    } else {
                        for (let i = 0; i < items.length; i++) {
                            const title = items[i].getElementsByTagName("title")[0].textContent;
                            const link = items[i].getElementsByTagName("link")[0].textContent;
                            const guid = items[i].getElementsByTagName("guid")[0].textContent;
                            const pubDate = items[i].getElementsByTagName("pubDate")[0].textContent;
                            
                            html += `<div class="item">
                                <h3><a href="${link}" target="_blank">${title}</a></h3>
                                <p>GUID: ${guid}</p>
                                <p>公開日: ${pubDate}</p>
                            </div>`;
                        }
                    }
                    
                    document.getElementById('entries').innerHTML = html;
                })
                .catch(error => {
                    document.getElementById('entries').innerHTML = `<p>エラーが発生しました: ${error}</p>`;
                });
        </script>
    </body>
    </html>
    """

@app.route('/')
def index():
    """アプリケーションのホームページ"""
    # 最終更新時刻を取得
    last_update = None
    with store_lock:
        if global_store['last_update'] is not None:
            last_update = global_store['last_update'].strftime("%Y-%m-%d %H:%M:%S")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>はてなブックマーク ホットエントリー RSS</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }}
            h1 {{
                color: #333;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }}
            code {{
                background-color: #f5f5f5;
                padding: 2px 5px;
                border-radius: 3px;
                font-family: monospace;
            }}
            .example {{
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .status {{
                color: #666;
                font-size: 0.9em;
                margin-top: 20px;
            }}
            .important {{
                color: #d9534f;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h1>はてなブックマーク ホットエントリー RSS</h1>
        <p>このサービスは、はてなブックマークのホットエントリーから指定したブックマーク数以上の記事をRSSフィードとして提供します。</p>
        
        <h2>使い方</h2>
        <p>以下のURLにアクセスすることで、RSSフィードを取得できます：</p>
        <div class="example">
            <code>{request.host_url}hotentry/all/feed?threshold=200</code>
        </div>
        
        <p><code>threshold</code>パラメータに数値を指定することで、そのブックマーク数以上の記事のみをフィルタリングできます。</p>
        
        <h2>IFTTT用エンドポイント</h2>
        <p>IFTTTのRSSトリガー用に、キャッシュなしのエンドポイントを提供しています：</p>
        <div class="example">
            <code>{request.host_url}hotentry/all/feed/nocache?threshold=200</code>
        </div>
        <p class="important">IFTTTを使用する場合は必ず上記の「nocache」エンドポイントを使用してください。</p>
        <p><a href="/debug/ifttt">IFTTTデバッグページ</a>でトラブルシューティングができます。</p>
        
        <h2>例</h2>
        <ul>
            <li><a href="{url_for('get_hotentry_feed', threshold=100)}" target="_blank">100ブックマーク以上の記事</a></li>
            <li><a href="{url_for('get_hotentry_feed', threshold=200)}" target="_blank">200ブックマーク以上の記事</a></li>
            <li><a href="{url_for('get_hotentry_feed', threshold=500)}" target="_blank">500ブックマーク以上の記事</a></li>
        </ul>
        
        <h2>特徴</h2>
        <ul>
            <li>はてなブックマークの説明文を<code>&lt;description&gt;</code>に含めます</li>
            <li>IFTTTのRSSトリガーに対応したフォーマット</li>
            <li>5分間隔で自動更新</li>
            <li>キャッシュありとキャッシュなしの2種類のエンドポイントを提供</li>
        </ul>
        
        <div class="status">
            <p>最終更新: {last_update or "更新情報なし"}</p>
        </div>
    </body>
    </html>
    """

def init_scheduler():
    """スケジューラーを初期化する"""
    if not scheduler.running:
        scheduler.add_job(
            update_global_store,
            trigger=IntervalTrigger(minutes=5),
            id='update_feed',
            name='Update RSS feed data',
            replace_existing=True
        )
        scheduler.start()
        app.logger.info("スケジューラーを開始しました")

# 初期データを取得
update_global_store()

# スケジューラーを初期化
init_scheduler()

# PythonAnywhere用のWSGIアプリケーション
application = app

# ローカル開発時のみ実行
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port)