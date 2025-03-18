"""Flaskアプリケーションのエントリーポイント。

このモジュールは、Renderでのデプロイ用のエントリーポイントです。
実際の実装は src/hatena_bookmark/app.py にあります。
"""

import os
import sys

# アプリケーションのパスを追加
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# src/hatena_bookmark/app.py からアプリケーションをインポート
try:
    from src.hatena_bookmark.app import app, application
except ImportError:
    # Renderでのデプロイ時のパス解決のため
    sys.path.insert(0, os.path.join(path, 'src'))
    from hatena_bookmark.app import app, application

# このモジュールが直接実行された場合
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port)