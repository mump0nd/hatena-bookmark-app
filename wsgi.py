"""WSGIアプリケーションエントリーポイント。

このモジュールは、Gunicornなどのウェブサーバーからアプリケーションを実行するためのエントリーポイントです。
"""

import sys
import os

# アプリケーションのパスを追加
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# アプリケーションをインポート
try:
    from src.hatena_bookmark.app import application
except ImportError:
    # Renderでのデプロイ時のパス解決のため
    sys.path.insert(0, os.path.join(path, 'src'))
    from hatena_bookmark.app import application