"""RSSフィード生成機能モジュール。

このモジュールは、はてなブックマークのホットエントリーからRSSフィードを生成する機能を提供します。
"""

import html
import logging
from flask import request, Response
from .api import fetch_hatena_hotentries
from .utils import format_rfc822_date

# ロガーの設定
logger = logging.getLogger(__name__)


def generate_rss_feed(entries, threshold):
    """エントリーからRSSフィードを生成する。

    Args:
        entries (list): エントリーのリスト
        threshold (int): ブックマーク数のしきい値

    Returns:
        str: XML形式のRSSフィード
    """
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


def get_hotentry_feed(threshold=100):
    """ホットエントリーのRSSフィードを生成する。

    Args:
        threshold (int, optional): ブックマーク数のしきい値。デフォルトは100。

    Returns:
        Response: XMLレスポンス
    """
    try:
        # 常に最新のデータを取得
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
    except Exception as e:
        logger.error(f"フィード生成中にエラーが発生しました: {str(e)}")
        error_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>エラー</title>
    <description>フィードの生成中にエラーが発生しました</description>
    <item>
      <title>エラーが発生しました</title>
      <description>{html.escape(str(e))}</description>
    </item>
  </channel>
</rss>"""
        return Response(error_xml, mimetype='application/xml', status=500)