"""ユーティリティ関数モジュール。

このモジュールには、アプリケーション全体で使用されるユーティリティ関数が含まれています。
主に日付変換や文字列処理などの汎用的な機能を提供します。
"""

import random
import email.utils
from datetime import datetime
from dateutil import parser


# User-Agentのリスト
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'
]


def get_random_user_agent():
    """ランダムなUser-Agentを返す。

    Returns:
        str: ランダムに選択されたUser-Agent文字列
    """
    return random.choice(USER_AGENTS)


def format_rfc822_date(date_str=None):
    """日付文字列をRFC822形式に変換する。

    Args:
        date_str (str, optional): 変換する日付文字列。Noneの場合は現在時刻を使用。

    Returns:
        str: RFC822形式の日付文字列
    """
    if date_str:
        try:
            dt = parser.parse(date_str)
        except Exception:
            dt = datetime.now()
    else:
        dt = datetime.now()
    return email.utils.format_datetime(dt)