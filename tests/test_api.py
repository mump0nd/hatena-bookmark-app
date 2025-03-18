"""APIモジュールのテスト。

このモジュールでは、はてなブックマークAPIとの通信機能をテストします。
"""

import unittest
from unittest.mock import patch, MagicMock
import xml.etree.ElementTree as ET
from src.hatena_bookmark.api import fetch_hatena_hotentries, fetch_hatena_hotentries_from_rss


class TestAPI(unittest.TestCase):
    """APIモジュールのテストクラス。"""

    @patch('src.hatena_bookmark.api.session.get')
    def test_fetch_hatena_hotentries_success(self, mock_get):
        """APIからのデータ取得が成功した場合のテスト。"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                'title': 'テスト記事1',
                'url': 'https://example.com/1',
                'description': 'テスト説明1',
                'count': 200,
                'date': '2023-01-01T00:00:00Z'
            },
            {
                'title': 'テスト記事2',
                'url': 'https://example.com/2',
                'description': 'テスト説明2',
                'count': 300,
                'date': '2023-01-02T00:00:00Z'
            }
        ]
        mock_get.return_value = mock_response

        # テスト対象の関数を実行
        result = fetch_hatena_hotentries()

        # 検証
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['title'], 'テスト記事1')
        self.assertEqual(result[1]['count'], 300)
        mock_get.assert_called_once()

    @patch('src.hatena_bookmark.api.session.get')
    def test_fetch_hatena_hotentries_failure(self, mock_get):
        """APIからのデータ取得が失敗した場合のテスト。"""
        # モックの設定
        mock_get.side_effect = Exception('API error')
        
        # フォールバック関数をモック
        with patch('src.hatena_bookmark.api.fetch_hatena_hotentries_from_rss') as mock_fallback:
            mock_fallback.return_value = [
                {
                    'title': 'フォールバック記事',
                    'url': 'https://example.com/fallback',
                    'description': 'フォールバック説明',
                    'count': 100,
                    'date': '2023-01-03T00:00:00Z'
                }
            ]
            
            # テスト対象の関数を実行
            result = fetch_hatena_hotentries()
            
            # 検証
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['title'], 'フォールバック記事')
            mock_fallback.assert_called_once()

    @patch('src.hatena_bookmark.api.session.get')
    def test_fetch_hatena_hotentries_from_rss(self, mock_get):
        """RSSフィードからのデータ取得をテスト。"""
        # モックの設定
        mock_response = MagicMock()
        
        # XMLレスポンスを作成
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <rdf:RDF
            xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
            xmlns:rss="http://purl.org/rss/1.0/"
            xmlns:dc="http://purl.org/dc/elements/1.1/"
            xmlns:content="http://purl.org/rss/1.0/modules/content/"
            xmlns:hatena="http://www.hatena.ne.jp/info/xmlns#">
            <rss:item>
                <rss:title>RSSテスト記事</rss:title>
                <rss:link>https://example.com/rss</rss:link>
                <rss:description>RSSテスト説明</rss:description>
                <dc:date>2023-01-04T00:00:00Z</dc:date>
                <hatena:bookmarkcount>150</hatena:bookmarkcount>
            </rss:item>
        </rdf:RDF>
        """
        mock_response.content = xml_content.encode('utf-8')
        mock_get.return_value = mock_response
        
        # テスト対象の関数を実行
        result = fetch_hatena_hotentries_from_rss()
        
        # 検証
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], 'RSSテスト記事')
        self.assertEqual(result[0]['count'], 150)
        mock_get.assert_called_once()


if __name__ == '__main__':
    unittest.main()