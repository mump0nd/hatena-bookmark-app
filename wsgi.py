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
from src.hatena_bookmark.app import application