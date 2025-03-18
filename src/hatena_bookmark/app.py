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
        <html lang="ja">
        <head>
            <title>IFTTT RSSトリガーデバッグ | はてなブックマークRSS</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --hatena-blue: #2468b7;
                    --hatena-light-blue: #e5f0fa;
                    --hatena-dark-blue: #1a4c80;
                    --accent-color: #ff4e2e;
                    --text-color: #333;
                    --light-gray: #f5f5f5;
                    --border-color: #ddd;
                }}
                
                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }}
                
                body {{
                    font-family: 'M PLUS Rounded 1c', 'Hiragino Kaku Gothic ProN', 'メイリオ', sans-serif;
                    color: var(--text-color);
                    line-height: 1.6;
                    background-color: #f9f9f9;
                    padding-bottom: 40px;
                }}
                
                header {{
                    background-color: var(--hatena-blue);
                    color: white;
                    padding: 1rem;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                
                nav {{
                    background-color: white;
                    padding: 0.5rem 1rem;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                
                nav ul {{
                    display: flex;
                    list-style: none;
                    justify-content: center;
                }}
                
                nav li {{
                    margin: 0 1rem;
                }}
                
                nav a {{
                    color: var(--hatena-blue);
                    text-decoration: none;
                    font-weight: bold;
                    transition: color 0.3s;
                }}
                
                nav a:hover {{
                    color: var(--accent-color);
                }}
                
                main {{
                    max-width: 800px;
                    margin: 2rem auto;
                    padding: 0 1rem;
                }}
                
                .card {{
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    padding: 1.5rem;
                    margin-bottom: 2rem;
                    transition: transform 0.3s, box-shadow 0.3s;
                }}
                
                .card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }}
                
                h1, h2, h3 {{
                    color: var(--hatena-blue);
                    margin-bottom: 1rem;
                }}
                
                h1 {{
                    font-size: 1.8rem;
                }}
                
                h2 {{
                    font-size: 1.5rem;
                    border-bottom: 2px solid var(--hatena-light-blue);
                    padding-bottom: 0.5rem;
                    margin-top: 2rem;
                }}
                
                p {{
                    margin-bottom: 1rem;
                }}
                
                code {{
                    background-color: var(--light-gray);
                    padding: 0.2rem 0.4rem;
                    border-radius: 4px;
                    font-family: monospace;
                    color: var(--accent-color);
                }}
                
                .example {{
                    background-color: var(--hatena-light-blue);
                    padding: 1rem;
                    border-radius: 8px;
                    margin: 1rem 0;
                    border-left: 4px solid var(--hatena-blue);
                }}
                
                ol, ul {{
                    margin-left: 1.5rem;
                    margin-bottom: 1rem;
                }}
                
                li {{
                    margin-bottom: 0.5rem;
                }}
                
                a {{
                    color: var(--hatena-blue);
                    text-decoration: none;
                    transition: color 0.3s;
                }}
                
                a:hover {{
                    color: var(--accent-color);
                    text-decoration: underline;
                }}
                
                .important {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 1rem;
                    margin: 1rem 0;
                    border-radius: 4px;
                }}
                
                .important::before {{
                    content: "⚠️ ";
                }}
                
                footer {{
                    text-align: center;
                    margin-top: 3rem;
                    color: #666;
                    font-size: 0.9rem;
                }}
            </style>
        </head>
        <body>
            <header>
                <h1>はてなブックマーク RSS ジェネレーター</h1>
            </header>
            
            <nav>
                <ul>
                    <li><a href="/">ホーム</a></li>
                    <li><a href="/debug/ifttt">IFTTTデバッグ</a></li>
                </ul>
            </nav>
            
            <main>
                <div class="card">
                    <h2>IFTTT RSSトリガーデバッグ</h2>
                    <p>このページは、IFTTTのRSSトリガーで問題が発生した場合のデバッグに使用します。</p>
                </div>
                
                <div class="card">
                    <h2>IFTTTでの設定方法</h2>
                    <ol>
                        <li>IFTTTで「RSS Feed」トリガーを選択</li>
                        <li>以下のURLを入力: <code>{request.host_url}hotentry/all/feed?threshold=200</code></li>
                        <li>「New feed item」を選択</li>
                        <li>任意のアクションを設定（例: Lineに通知）</li>
                    </ol>
                </div>
                
                <div class="card">
                    <h2>トラブルシューティング</h2>
                    <ol>
                        <li>URLが正しいか確認（特に末尾のスラッシュ）</li>
                        <li>しきい値が適切か確認（あまり高いと記事が少なくなる）</li>
                        <li>IFTTTの「Check now」ボタンを押して手動で確認</li>
                    </ol>
                </div>
                
                <div class="card">
                    <h2>RSSフィードの確認方法</h2>
                    <p>以下のリンクで直接RSSフィードを確認できます：</p>
                    <ul>
                        <li><a href="/hotentry/all/feed?threshold=100" target="_blank">100ブックマーク以上</a></li>
                        <li><a href="/hotentry/all/feed?threshold=200" target="_blank">200ブックマーク以上</a></li>
                    </ul>
                    
                    <div class="important">
                        <p>IFTTTでは「New feed item」トリガーを使用し、頻繁に更新されるアイテムを検出するためには、アプレットを一度無効にしてから再度有効にすると良いことがあります。</p>
                    </div>
                </div>
            </main>
            
            <footer>
                <p>© 2025 はてなブックマーク RSS ジェネレーター</p>
            </footer>
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
        <html lang="ja">
        <head>
            <title>はてなブックマーク ホットエントリー RSS</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --hatena-blue: #2468b7;
                    --hatena-light-blue: #e5f0fa;
                    --hatena-dark-blue: #1a4c80;
                    --accent-color: #ff4e2e;
                    --text-color: #333;
                    --light-gray: #f5f5f5;
                    --border-color: #ddd;
                }}
                
                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }}
                
                body {{
                    font-family: 'M PLUS Rounded 1c', 'Hiragino Kaku Gothic ProN', 'メイリオ', sans-serif;
                    color: var(--text-color);
                    line-height: 1.6;
                    background-color: #f9f9f9;
                    padding-bottom: 40px;
                }}
                
                header {{
                    background-color: var(--hatena-blue);
                    color: white;
                    padding: 1.5rem;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    position: relative;
                    overflow: hidden;
                }}
                
                header::before {{
                    content: "";
                    position: absolute;
                    top: -10px;
                    left: -10px;
                    right: -10px;
                    bottom: -10px;
                    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 50%);
                    z-index: 1;
                }}
                
                header h1 {{
                    position: relative;
                    z-index: 2;
                    color: white;
                    margin: 0;
                    font-size: 2rem;
                }}
                
                nav {{
                    background-color: white;
                    padding: 0.5rem 1rem;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                
                nav ul {{
                    display: flex;
                    list-style: none;
                    justify-content: center;
                }}
                
                nav li {{
                    margin: 0 1rem;
                }}
                
                nav a {{
                    color: var(--hatena-blue);
                    text-decoration: none;
                    font-weight: bold;
                    transition: color 0.3s;
                }}
                
                nav a:hover {{
                    color: var(--accent-color);
                }}
                
                main {{
                    max-width: 800px;
                    margin: 2rem auto;
                    padding: 0 1rem;
                }}
                
                .card {{
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    padding: 1.5rem;
                    margin-bottom: 2rem;
                    transition: transform 0.3s, box-shadow 0.3s;
                }}
                
                .card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }}
                
                h1, h2, h3 {{
                    color: var(--hatena-blue);
                    margin-bottom: 1rem;
                }}
                
                h2 {{
                    font-size: 1.5rem;
                    border-bottom: 2px solid var(--hatena-light-blue);
                    padding-bottom: 0.5rem;
                    margin-top: 1rem;
                }}
                
                p {{
                    margin-bottom: 1rem;
                }}
                
                code {{
                    background-color: var(--light-gray);
                    padding: 0.2rem 0.4rem;
                    border-radius: 4px;
                    font-family: monospace;
                    color: var(--accent-color);
                }}
                
                .example {{
                    background-color: var(--hatena-light-blue);
                    padding: 1rem;
                    border-radius: 8px;
                    margin: 1rem 0;
                    border-left: 4px solid var(--hatena-blue);
                }}
                
                ol, ul {{
                    margin-left: 1.5rem;
                    margin-bottom: 1rem;
                }}
                
                li {{
                    margin-bottom: 0.5rem;
                }}
                
                a {{
                    color: var(--hatena-blue);
                    text-decoration: none;
                    transition: color 0.3s;
                }}
                
                a:hover {{
                    color: var(--accent-color);
                    text-decoration: underline;
                }}
                
                .feature-list {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 1rem;
                    margin-top: 1rem;
                }}
                
                .feature-item {{
                    background-color: var(--hatena-light-blue);
                    padding: 1rem;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                }}
                
                .feature-item::before {{
                    content: "✓";
                    display: inline-block;
                    margin-right: 0.5rem;
                    color: var(--hatena-blue);
                    font-weight: bold;
                }}
                
                .status {{
                    background-color: var(--light-gray);
                    padding: 0.5rem 1rem;
                    border-radius: 4px;
                    margin-top: 1rem;
                    font-size: 0.9rem;
                    color: #666;
                }}
                
                .support {{
                    margin-top: 2rem;
                    text-align: center;
                    padding: 1rem;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                
                .support p {{
                    margin-bottom: 1rem;
                    color: #666;
                }}
                
                .btn {{
                    display: inline-block;
                    background-color: var(--hatena-blue);
                    color: white;
                    padding: 0.5rem 1rem;
                    border-radius: 4px;
                    text-decoration: none;
                    transition: background-color 0.3s;
                }}
                
                .btn:hover {{
                    background-color: var(--hatena-dark-blue);
                    text-decoration: none;
                }}
                
                footer {{
                    text-align: center;
                    margin-top: 3rem;
                    color: #666;
                    font-size: 0.9rem;
                }}
                
                @media (max-width: 600px) {{
                    .feature-list {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <header>
                <h1>はてなブックマーク ホットエントリー RSS</h1>
            </header>
            
            <nav>
                <ul>
                    <li><a href="/">ホーム</a></li>
                    <li><a href="/debug/ifttt">IFTTTデバッグ</a></li>
                </ul>
            </nav>
            
            <main>
                <div class="card">
                    <p>このサービスは、はてなブックマークのホットエントリーから指定したブックマーク数以上の記事をRSSフィードとして提供します。IFTTTと連携して、新しい人気記事の通知を自動化できます。</p>
                </div>
                
                <div class="card">
                    <h2>使い方</h2>
                    <p>以下のURLにアクセスすることで、RSSフィードを取得できます：</p>
                    <div class="example">
                        <code>{request.host_url}hotentry/all/feed?threshold=200</code>
                    </div>
                    
                    <p><code>threshold</code>パラメータに数値を指定することで、そのブックマーク数以上の記事のみをフィルタリングできます。</p>
                </div>
                
                <div class="card">
                    <h2>IFTTT用エンドポイント</h2>
                    <p>IFTTTのRSSトリガー用に最適化されたエンドポイントを提供しています：</p>
                    <div class="example">
                        <code>{request.host_url}hotentry/all/feed?threshold=200</code>
                    </div>
                    <p><a href="/debug/ifttt" class="btn">IFTTTデバッグページ</a></p>
                </div>
                
                <div class="card">
                    <h2>例</h2>
                    <ul>
                        <li><a href="{url_for('hotentry_feed', threshold=100)}" target="_blank">100ブックマーク以上の記事</a></li>
                        <li><a href="{url_for('hotentry_feed', threshold=200)}" target="_blank">200ブックマーク以上の記事</a></li>
                        <li><a href="{url_for('hotentry_feed', threshold=500)}" target="_blank">500ブックマーク以上の記事</a></li>
                    </ul>
                </div>
                
                <div class="card">
                    <h2>特徴</h2>
                    <div class="feature-list">
                        <div class="feature-item">はてなブックマークの説明文を含む</div>
                        <div class="feature-item">IFTTTのRSSトリガーに対応</div>
                        <div class="feature-item">常に最新のデータを取得</div>
                        <div class="feature-item">5分間隔でデータ更新</div>
                    </div>
                    
                    <div class="status">
                        <p>最終更新: {last_update or "更新情報なし"}</p>
                    </div>
                </div>
                
                <div class="support">
                    <p>このサービスが役立つと感じたら、開発者をサポートしてください</p>
                    <a href="https://www.buymeacoffee.com/mump0nd" target="_blank">
                        <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;">
                    </a>
                </div>
            </main>
            
            <footer>
                <p>© 2025 はてなブックマーク RSS ジェネレーター</p>
            </footer>
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