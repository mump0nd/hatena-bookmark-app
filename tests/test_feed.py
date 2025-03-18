"""フィード生成モジュールのテスト。

このモジュールでは、RSSフィード生成機能をテストします。
"""

import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Response
from src.hatena_bookmark.feed import generate_rss_feed, get_hotentry_feed


class TestFeed(unittest.TestCase):
    """フィード生成モジュールのテストクラス。"""

    def setUp(self):
        """テスト前の準備。"""
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.request_context = self.app.test_request_context('http://example.com/hotentry/all/feed?threshold=200')
        self.request_context.push()
        
        # テスト用のエントリーデータ
        self.test_entries = [
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

    def tearDown(self):
        """テスト後のクリーンアップ。"""
        self.request_context.pop()
        self.app_context.pop()

    def test_generate_rss_feed(self):
        """RSSフィード生成のテスト。"""
        # テスト対象の関数を実行
        result = generate_rss_feed(self.test_entries, 200)
        
        # 検証
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
        self.assertIn('<title>Hatena Hotentry (Threshold: 200)</title>', result)
        self.assertIn('<title>テスト記事1</title>', result)
        self.assertIn('<title>テスト記事2</title>', result)
        self.assertIn('ブックマーク数: 200', result)
        self.assertIn('ブックマーク数: 300', result)

    @patch('src.hatena_bookmark.feed.fetch_hatena_hotentries')
    def test_get_hotentry_feed_success(self, mock_fetch):
        """ホットエントリーフィード取得成功のテスト。"""
        # モックの設定
        mock_fetch.return_value = self.test_entries
        
        # テスト対象の関数を実行
        result = get_hotentry_feed(200)
        
        # 検証
        self.assertIsInstance(result, Response)
        self.assertEqual(result.mimetype, 'application/xml')
        self.assertEqual(result.status_code, 200)
        mock_fetch.assert_called_once()

    @patch('src.hatena_bookmark.feed.fetch_hatena_hotentries')
    def test_get_hotentry_feed_filtering(self, mock_fetch):
        """ブックマーク数によるフィルタリングのテスト。"""
        # モックの設定
        mock_fetch.return_value = [
            {'title': '記事1', 'url': 'https://example.com/1', 'description': '説明1', 'count': 100, 'date': '2023-01-01T00:00:00Z'},
            {'title': '記事2', 'url': 'https://example.com/2', 'description': '説明2', 'count': 200, 'date': '2023-01-02T00:00:00Z'},
            {'title': '記事3', 'url': 'https://example.com/3', 'description': '説明3', 'count': 300, 'date': '2023-01-03T00:00:00Z'}
        ]
        
        # テスト対象の関数を実行（しきい値200）
        result = get_hotentry_feed(200)
        
        # 検証（記事2と記事3のみが含まれるはず）
        content = result.get_data(as_text=True)
        self.assertNotIn('<title>記事1</title>', content)
        self.assertIn('<title>記事2</title>', content)
        self.assertIn('<title>記事3</title>', content)

    @patch('src.hatena_bookmark.feed.fetch_hatena_hotentries')
    def test_get_hotentry_feed_error(self, mock_fetch):
        """エラー発生時のテスト。"""
        # モックの設定
        mock_fetch.side_effect = Exception('テストエラー')
        
        # テスト対象の関数を実行
        result = get_hotentry_feed(200)
        
        # 検証
        self.assertIsInstance(result, Response)
        self.assertEqual(result.mimetype, 'application/xml')
        self.assertEqual(result.status_code, 500)
        content = result.get_data(as_text=True)
        self.assertIn('<title>エラー</title>', content)
        self.assertIn('<title>エラーが発生しました</title>', content)
        self.assertIn('テストエラー', content)


if __name__ == '__main__':
    unittest.main()