"""はてなブックマークAPIとの通信機能モジュール。

このモジュールは、はてなブックマークのAPIやRSSフィードからデータを取得する機能を提供します。
APIアクセスに失敗した場合は、RSSフィードからのフォールバック機能も実装しています。
"""

import requests
import xml.etree.ElementTree as ET
import logging
from .utils import get_random_user_agent

# リクエストセッション
session = requests.Session()
session.headers.update({
    'Accept': 'application/json, text/xml',
    'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
})

# ロガーの設定
logger = logging.getLogger(__name__)


def fetch_hatena_hotentries():
    """はてなブックマークのホットエントリーを取得する。

    APIからデータを取得し、失敗した場合はRSSフィードからデータを取得します。

    Returns:
        list: エントリーのリスト。各エントリーは辞書形式で、title, url, description, count, dateを含む。

    Raises:
        requests.RequestException: リクエストに失敗した場合
    """
    try:
        # APIからデータを取得
        url = "https://b.hatena.ne.jp/api/ipad.hotentry?mode=general"
        session.headers['User-Agent'] = get_random_user_agent()
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"APIからのデータ取得に失敗しました: {str(e)}")
        # 失敗した場合はRSSフィードから取得
        return fetch_hatena_hotentries_from_rss()


def fetch_hatena_hotentries_from_rss():
    """はてなブックマークのホットエントリーをRSSフィードから取得する。

    Returns:
        list: エントリーのリスト。各エントリーは辞書形式で、title, url, description, count, dateを含む。

    Raises:
        requests.RequestException: リクエストに失敗した場合
    """
    url = "https://b.hatena.ne.jp/hotentry.rss"
    session.headers['User-Agent'] = get_random_user_agent()
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