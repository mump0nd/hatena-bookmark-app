import sys
import os

# アプリケーションのパスを追加
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# 仮想環境のサイトパッケージを追加（PythonAnywhereでの設定例）
venv_path = os.path.join(path, 'venv')
site_packages = os.path.join(venv_path, 'lib', 'python3.9', 'site-packages')
if os.path.exists(site_packages) and site_packages not in sys.path:
    sys.path.append(site_packages)

# アプリケーションをインポート
from app import application