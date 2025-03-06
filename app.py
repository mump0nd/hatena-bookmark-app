from flask import Flask, request, Response, url_for
import requests
import json
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time
from dateutil import parser
import re
from functools import wraps
import threading
import html
import os

app = Flask(__name__)

# キャッシュを保持するための辞書
cache = {}
cache_lock = threading.Lock()

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

def fetch_hatena_hotentries():
    """はてなブックマークのホットエントリーを取得する"""
    url = "https://b.hatena.ne.jp/api/ipad.hotentry?mode=general"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()

def get_article_first_paragraphs(url, max_paragraphs=3):
    """記事のURLから最初の3つの段落を取得する"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # html.parserを使用してBeautifulSoupオブジェクトを作成
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 記事の本文から最初の3つの段落を取得
        paragraphs = soup.find_all('p')
        
        # テキストが空でない段落のみを抽出
        valid_paragraphs = []
        for p in paragraphs:
            text = p.get_text().strip()
            if text and len(text) > 20:  # 短すぎる段落は除外
                valid_paragraphs.append(text)
                if len(valid_paragraphs) >= max_paragraphs:
                    break
        
        if valid_paragraphs:
            return "\n\n".join(valid_paragraphs)
        else:
            # 段落が見つからない場合はメタディスクリプションを試す
            meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
            if meta_desc and meta_desc.get('content'):
                return meta_desc.get('content')
            
            return "記事の概要を取得できませんでした"
    except Exception as e:
        app.logger.error(f"記事の取得中にエラーが発生しました: {str(e)}")
        return "記事の概要を取得できませんでした"

def generate_rss_feed(entries, threshold):
    """エントリーからRSSフィードを生成する（文字列操作でXMLを生成）"""
    current_time = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
    
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
    
    # 各エントリー
    for entry in entries:
        xml += '    <item>\n'
        xml += f'      <title>{html.escape(entry.get("title", "無題"))}</title>\n'
        xml += f'      <link>{html.escape(entry.get("link", ""))}</link>\n'
        xml += f'      <guid isPermaLink="true">{html.escape(entry.get("link", ""))}</guid>\n'
        xml += f'      <description>{html.escape(entry.get("description", ""))}</description>\n'
        xml += '      <content:encoded><![CDATA[\n'
        xml += f'        {entry.get("content_html", "")}\n'
        xml += '      ]]></content:encoded>\n'
        xml += f'      <pubDate>{entry.get("date", current_time)}</pubDate>\n'
        xml += '    </item>\n'
    
    # 終了タグ
    xml += '  </channel>\n'
    xml += '</rss>'
    
    return xml

@app.route('/hotentry/all/feed')
@with_cache(600)  # 10分間キャッシュ
def get_hotentry_feed():
    """ホットエントリーのRSSフィードを返す"""
    # クエリパラメータからしきい値を取得（デフォルトは100）
    threshold = request.args.get('threshold', '100')
    try:
        threshold = int(threshold)
    except ValueError:
        threshold = 100
    
    # はてなブックマークのホットエントリーを取得
    entries = fetch_hatena_hotentries()
    
    # しきい値以上のブックマーク数を持つエントリーをフィルタリング
    filtered_entries = []
    
    for entry in entries:
        # ブックマーク数を取得
        bookmark_count = entry.get('count', 0)
        
        if bookmark_count >= threshold:
            # 記事の冒頭3行を取得
            article_paragraphs = get_article_first_paragraphs(entry.get('url', ''))
            
            # HTMLコンテンツを作成
            content_html = ""
            for paragraph in article_paragraphs.split("\n\n"):
                if paragraph:
                    content_html += f"<p>{paragraph}</p>\n"
            
            # エントリー情報を整形
            formatted_entry = {
                'title': entry.get('title', '無題'),
                'link': entry.get('url', ''),
                'description': article_paragraphs,
                'content_html': content_html,
                'date': entry.get('date', datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"))
            }
            
            filtered_entries.append(formatted_entry)
    
    # RSSフィードを生成
    rss_feed = generate_rss_feed(filtered_entries, threshold)
    
    # XMLレスポンスを返す
    return Response(rss_feed, mimetype='application/xml')

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
        
        <h2>例</h2>
        <ul>
            <li><a href="{url_for('get_hotentry_feed', threshold=100)}" target="_blank">100ブックマーク以上の記事</a></li>
            <li><a href="{url_for('get_hotentry_feed', threshold=200)}" target="_blank">200ブックマーク以上の記事</a></li>
            <li><a href="{url_for('get_hotentry_feed', threshold=500)}" target="_blank">500ブックマーク以上の記事</a></li>
        </ul>
        
        <h2>特徴</h2>
        <ul>
            <li>記事の冒頭3段落を<code>&lt;description&gt;</code>に含めます</li>
            <li>リッチなHTMLコンテンツを<code>&lt;content:encoded&gt;</code>に含めます</li>
            <li>10分間のキャッシュ機能により、サーバーの負荷を軽減します</li>
        </ul>
    </body>
    </html>
    """

# PythonAnywhere用のWSGIアプリケーション
application = app

if __name__ == '__main__':
    # ローカル開発時
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port)
else:
    # 本番環境（PythonAnywhereなど）
    app.run(debug=False)