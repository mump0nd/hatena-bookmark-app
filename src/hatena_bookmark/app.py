"""Flaskアプリケーションの定義とルーティングモジュール。

このモジュールは、Flaskアプリケーションの初期化、ルーティング、およびバックグラウンドタスクの
設定を行います。
"""

import os
import threading
import logging
from datetime import datetime
from flask import Flask, url_for, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .feed import get_hotentry_feed
from .api import fetch_hatena_hotentries

# グローバルなデータストア
global_store = {
    'latest_entries': None,
    'last_update': None
}
store_lock = threading.Lock()

# スケジューラーの初期化
scheduler = BackgroundScheduler()

# ロガーの設定
logger = logging.getLogger(__name__)


def create_app():
    """Flaskアプリケーションを作成する。

    Returns:
        Flask: 設定済みのFlaskアプリケーション
    """
    app = Flask(__name__)
    
    # ルーティングの設定
    @app.route('/hotentry/all/feed')
    def hotentry_feed():
        """ホットエントリーのRSSフィードを返す（常に最新データを取得）。

        Returns:
            Response: XMLレスポンス
        """
        # クエリパラメータからしきい値を取得（デフォルトは100）
        threshold = request.args.get('threshold', '100')
        try:
            threshold = int(threshold)
        except ValueError:
            threshold = 100
        
        return get_hotentry_feed(threshold)
    
    # 互換性のために古いエンドポイントも維持
    @app.route('/hotentry/all/feed/nocache')
    def hotentry_feed_nocache():
        """ホットエントリーのRSSフィードを返す（IFTTT用、/hotentry/all/feedにリダイレクト）。

        Returns:
            Response: XMLレスポンス
        """
        # クエリパラメータからしきい値を取得
        threshold = request.args.get('threshold', '100')
        try:
            threshold = int(threshold)
        except ValueError:
            threshold = 100
        
        return get_hotentry_feed(threshold)
    
    @app.route('/debug/ifttt')
    def debug_ifttt():
        """IFTTTデバッグ用のエンドポイント（簡素化版）。

        Returns:
            str: HTMLレスポンス
        """
        # サンプルデータを用意（APIリクエストなし）
        threshold = 200
        
        # スタティックなHTMLを返す
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>IFTTT RSSトリガーデバッグ</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                pre {{ background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                .item {{ border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .important {{ color: #d9534f; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>IFTTT RSSトリガーデバッグ</h1>
            <p>このページは、IFTTTのRSSトリガーで問題が発生した場合のデバッグに使用します。</p>
            
            <h2>IFTTTでの設定方法</h2>
            <ol>
                <li>IFTTTで「RSS Feed」トリガーを選択</li>
                <li>以下のURLを入力: <code>{request.host_url}hotentry/all/feed?threshold=200</code></li>
                <li>「New feed item」を選択</li>
                <li>任意のアクションを設定（例: Lineに通知）</li>
            </ol>
            
            <h2>トラブルシューティング</h2>
            <ol>
                <li>URLが正しいか確認（特に末尾のスラッシュ）</li>
                <li>しきい値が適切か確認（あまり高いと記事が少なくなる）</li>
                <li>IFTTTの「Check now」ボタンを押して手動で確認</li>
            </ol>
            
            <h2>RSSフィードの確認方法</h2>
            <p>以下のリンクで直接RSSフィードを確認できます：</p>
            <ul>
                <li><a href="/hotentry/all/feed?threshold=100" target="_blank">100ブックマーク以上</a></li>
                <li><a href="/hotentry/all/feed?threshold=200" target="_blank">200ブックマーク以上</a></li>
            </ul>
            
            <p class="important">注意: IFTTTでは「New feed item」トリガーを使用し、頻繁に更新されるアイテムを検出するためには、アプレットを一度無効にしてから再度有効にすると良いことがあります。</p>
        </body>
        </html>
        """
    
    @app.route('/')
    def index():
        """アプリケーションのホームページ。

        Returns:
            str: HTMLレスポンス
        """
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
                .support {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    text-align: center;
                }}
                .support p {{
                    margin-bottom: 15px;
                    color: #666;
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
            <p>IFTTTのRSSトリガー用に最適化されたエンドポイントを提供しています：</p>
            <div class="example">
                <code>{request.host_url}hotentry/all/feed?threshold=200</code>
            </div>
            <p><a href="/debug/ifttt">IFTTTデバッグページ</a>でトラブルシューティングができます。</p>
            
            <h2>例</h2>
            <ul>
                <li><a href="{url_for('hotentry_feed', threshold=100)}" target="_blank">100ブックマーク以上の記事</a></li>
                <li><a href="{url_for('hotentry_feed', threshold=200)}" target="_blank">200ブックマーク以上の記事</a></li>
                <li><a href="{url_for('hotentry_feed', threshold=500)}" target="_blank">500ブックマーク以上の記事</a></li>
            </ul>
            
            <h2>特徴</h2>
            <ul>
                <li>はてなブックマークの説明文を<code>&lt;description&gt;</code>に含めます</li>
                <li>IFTTTのRSSトリガーに対応したフォーマット</li>
                <li>常に最新のデータを取得（キャッシュなし）</li>
                <li>5分間隔でバックグラウンドデータ更新</li>
            </ul>
            
            <div class="status">
                <p>最終更新: {last_update or "更新情報なし"}</p>
            </div>
            
            <div class="support">
                <p>このサービスが役立つと感じたら、開発者をサポートしてください</p>
                <a href="https://www.buymeacoffee.com/mump0nd" target="_blank">
                    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;">
                </a>
            </div>
        </body>
        </html>
        """
    
    @app.route('/health')
    def health_check():
        """ヘルスチェックエンドポイント。

        Returns:
            tuple: レスポンス文字列とステータスコード
        """
        return "OK", 200
    
    return app


def update_global_store():
    """グローバルストアのデータを更新する。"""
    try:
        entries = fetch_hatena_hotentries()
        with store_lock:
            global_store['latest_entries'] = entries
            global_store['last_update'] = datetime.now()
        logger.info("グローバルストアのデータを更新しました")
    except Exception as e:
        logger.error(f"グローバルストアの更新に失敗しました: {str(e)}")


def init_scheduler():
    """スケジューラーを初期化する。"""
    if not scheduler.running:
        scheduler.add_job(
            update_global_store,
            trigger=IntervalTrigger(minutes=5),
            id='update_feed',
            name='Update RSS feed data',
            replace_existing=True
        )
        scheduler.start()
        logger.info("スケジューラーを開始しました")


# アプリケーションの初期化
app = create_app()

# 初期データを取得
try:
    update_global_store()
except Exception as e:
    logger.error(f"初期データ取得に失敗しました: {str(e)}")

# スケジューラーを初期化
try:
    init_scheduler()
except Exception as e:
    logger.error(f"スケジューラーの初期化に失敗しました: {str(e)}")

# Render用のWSGIアプリケーション
application = app

# ローカル開発時のみ実行
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port)