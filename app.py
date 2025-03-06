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

app = Flask(__name__)

# キャッシュを保持するための辞書
cache = {}
cache_lock = threading.Lock()

# User-Agentのリスト
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
]

# リクエストセッション
session = requests.Session()
session.headers.update({
    'Accept': 'application/json, text/xml',
    'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
})

def get_cache_key(threshold):
    """キャッシュキーを生成する"""
    return f"threshold_{threshold}"

def with_cache(expiration=600):  # デフォルトの有効期限は10分（600秒）
    """キャッシュ機能を提供するデコレータ"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            threshold = kwargs.get('threshold', request.args.get('threshold', '100'))
            cache_key = get_cache_key(threshold)
            
            with cache_lock:
                # キャッシュが存在し、有効期限内であれば、キャッシュから返す
                if cache_key in cache and cache[cache_key]['expires'] > time.time():
                    app.logger.info(f"キャッシュからデータを返します (threshold={threshold})")
                    return cache[cache_key]['data']
            
            # キャッシュがない場合や期限切れの場合は、元の関数を実行
            result = f(*args, **kwargs)
            
            # 結果をキャッシュに保存
            with cache_lock:
                cache[cache_key] = {
                    'data': result,
                    'expires': time.time() + expiration
                }
            
            return result
        return decorated_function
    return decorator

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
        response = session.get(url, timeout=5)
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
    response = session.get(url, timeout=5)
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

def generate_rss_feed(entries, threshold):
    """エントリーからRSSフィードを生成する（文字列操作でXMLを生成）"""
    current_time = format_rfc822_date()
    
    # XMLヘッダーとRSS開始タグ
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:atom="http://www.w3.org/2005/Atom">\n'
    xml += '  <channel>\n'
    
    # チャンネル情報
    xml += f'    <title>Hatena Hotentry (Threshold: {threshold})</title>\n'
    xml += f'    <link>{html.escape(request.url)}</link>\n'
    xml += f'    <description>はてなブックマークの人気エントリー（{threshold}ブックマーク以上）</description>\n'
    xml += '    <language>ja</language>\n'
    xml += f'    <lastBuildDate>{current_time}</lastBuildDate>\n'
    xml += f'    <atom:link href="{html.escape(request.url)}" rel="self" type="application/rss+xml"/>\n'
    xml += '    <ttl>10</ttl>\n'  # TTLを10分に設定
    
    # 各エントリー
    for entry in entries:
        # 日付をRFC822形式に変換
        pub_date = format_rfc822_date(entry.get('date'))
        
        xml += '    <item>\n'
        xml += f'      <title>{html.escape(entry.get("title", "無題"))}</title>\n'
        xml += f'      <link>{html.escape(entry.get("url", ""))}</link>\n'
        xml += f'      <guid isPermaLink="true">{html.escape(entry.get("url", ""))}</guid>\n'
        xml += f'      <description>{html.escape(entry.get("description", ""))}</description>\n'
        xml += f'      <pubDate>{pub_date}</pubDate>\n'
        xml += '    </item>\n'
    
    # 終了タグ
    xml += '  </channel>\n'
    xml += '</rss>'
    
    return xml

def get_hotentry_feed_internal(threshold=100):
    """ホットエントリーのRSSフィードを生成する内部関数"""
    # はてなブックマークのホットエントリーを取得
    entries = fetch_hatena_hotentries()
    
    # しきい値以上のブックマーク数を持つエントリーをフィルタリング
    filtered_entries = []
    
    for entry in entries:
        # ブックマーク数を取得
        bookmark_count = entry.get('count', 0)
        
        if bookmark_count >= threshold:
            # エントリー情報を整形
            formatted_entry = {
                'title': entry.get('title', '無題'),
                'url': entry.get('url', ''),
                'description': entry.get('description', '説明なし'),
                'date': entry.get('date', datetime.now().isoformat())
            }
            
            filtered_entries.append(formatted_entry)
    
    # RSSフィードを生成
    rss_feed = generate_rss_feed(filtered_entries, threshold)
    
    # XMLレスポンスを返す
    return Response(rss_feed, mimetype='application/xml')

@app.route('/hotentry/all/feed')
@with_cache(600)  # 10分間キャッシュ
def get_hotentry_feed():
    """ホットエントリーのRSSフィードを返す（キャッシュあり）"""
    # クエリパラメータからしきい値を取得（デフォルトは100）
    threshold = request.args.get('threshold', '100')
    try:
        threshold = int(threshold)
    except ValueError:
        threshold = 100
    
    return get_hotentry_feed_internal(threshold)

@app.route('/hotentry/all/feed/nocache')
def get_hotentry_feed_nocache():
    """ホットエントリーのRSSフィードを返す（キャッシュなし、IFTTT用）"""
    # クエリパラメータからしきい値を取得（デフォルトは100）
    threshold = request.args.get('threshold', '100')
    try:
        threshold = int(threshold)
    except ValueError:
        threshold = 100
    
    return get_hotentry_feed_internal(threshold)

@app.route('/')
def index():
    """アプリケーションのホームページ"""
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
            <li>キャッシュありとキャッシュなしの2種類のエンドポイントを提供</li>
        </ul>
    </body>
    </html>
    """

# PythonAnywhere用のWSGIアプリケーション
application = app

# ローカル開発時のみ実行
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port)