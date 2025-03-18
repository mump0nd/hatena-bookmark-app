# Render CLI を使用したログ確認ガイド

このドキュメントでは、Render CLI をインストールし、はてなブックマーク RSS ジェネレーターのログを確認する方法について説明します。

## Render CLI のインストール

### 前提条件

- Node.js と npm がインストールされていること

### インストール手順

1. npm を使用して Render CLI をグローバルにインストールします：

```bash
npm install -g @render/cli
```

2. インストールが完了したら、バージョンを確認してインストールが正常に行われたことを確認します：

```bash
render --version
```

## Render アカウントへのログイン

1. 以下のコマンドを実行して、Render アカウントにログインします：

```bash
render login
```

2. ブラウザが自動的に開き、Render の認証ページが表示されます。
3. Render アカウントでログインし、CLI へのアクセスを許可します。
4. 認証が成功すると、ターミナルに成功メッセージが表示されます。

## サービスの一覧表示

1. Render アカウントに関連付けられているサービスの一覧を表示します：

```bash
render list services
```

2. 出力から、はてなブックマーク RSS ジェネレーターのサービス ID またはサービス名を確認します。

## ログの確認

### リアルタイムログの表示

サービスのリアルタイムログを表示するには、以下のコマンドを実行します：

```bash
render logs <サービス名またはサービスID>
```

例：

```bash
render logs hatena-bookmark-app
```

これにより、サービスのログがリアルタイムで表示されます。ログの表示を停止するには、`Ctrl+C` を押します。

### 過去のログの表示

過去のログを表示するには、`--since` オプションを使用します：

```bash
render logs <サービス名またはサービスID> --since 1h
```

時間の指定方法：
- `5m`: 5分前から
- `1h`: 1時間前から
- `1d`: 1日前から
- `2023-01-01T00:00:00Z`: 特定の日時から（ISO 8601形式）

### ログのフィルタリング

特定のキーワードでログをフィルタリングするには、`--filter` オプションを使用します：

```bash
render logs <サービス名またはサービスID> --filter "error"
```

これにより、「error」という単語を含むログエントリのみが表示されます。

### ログの保存

ログをファイルに保存するには、出力をリダイレクトします：

```bash
render logs <サービス名またはサービスID> --since 1d > logs.txt
```

## デプロイの確認

最近のデプロイを確認するには、以下のコマンドを実行します：

```bash
render list deploys <サービス名またはサービスID>
```

## 代替ログ確認方法

Render CLIが利用できない場合や、Node.jsがインストールされていない環境では、以下の代替方法でログを確認できます：

### 1. Renderダッシュボードを使用する方法

最も簡単な方法は、Renderのウェブダッシュボードを使用することです：

1. Renderダッシュボード（https://dashboard.render.com/）にログイン
2. サービス「hatena-bookmark-app」を選択
3. 「Logs」タブをクリック
4. リアルタイムログを確認

### 2. SSH接続を使用する方法

RenderはサービスへのアクセスにSSH接続も提供しています：

1. Renderダッシュボードでサービスを選択
2. 「Settings」タブをクリック
3. 「SSH Public Key」セクションでSSH公開鍵を追加
4. サービス情報から取得したSSHアドレスに接続：
   ```bash
   ssh srv-cv4jaaaj1k6c738o8bi0@ssh.oregon.render.com
   ```
5. 接続後、`logs`コマンドを実行してログを表示

### 3. Render APIを使用する方法

Render APIを使用してサービス情報を取得できますが、現在のAPIバージョンではログの直接取得はサポートされていません：

```bash
# サービス情報の取得
curl -H "Authorization: Bearer YOUR_API_TOKEN" https://api.render.com/v1/services/YOUR_SERVICE_ID

# デプロイ一覧の取得
curl -H "Authorization: Bearer YOUR_API_TOKEN" https://api.render.com/v1/services/YOUR_SERVICE_ID/deploys
```

## トラブルシューティング

### 認証エラー

認証エラーが発生した場合は、再度ログインを試みてください：

```bash
render logout
render login
```

### API レート制限

API レート制限に達した場合は、しばらく待ってから再試行してください。

### Node.jsがインストールされていない

Node.jsがインストールされていない環境では、以下の手順でインストールできます：

#### macOS

```bash
# Homebrewを使用する場合
brew install node

# nvmを使用する場合
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
nvm install --lts
```

#### Linux (Ubuntu/Debian)

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### Windows

Node.jsの公式サイト（https://nodejs.org/）からインストーラーをダウンロードしてインストールします。

### その他の問題

その他の問題が発生した場合は、Render のドキュメントを参照するか、サポートに問い合わせてください：

- [Render CLI ドキュメント](https://render.com/docs/cli)
- [Render サポート](https://render.com/docs/support)

## 便利なコマンド集

### サービスの再起動

```bash
render restart <サービス名またはサービスID>
```

### サービスの情報表示

```bash
render info <サービス名またはサービスID>
```

### 環境変数の一覧表示

```bash
render env list <サービス名またはサービスID>
```

### 環境変数の設定

```bash
render env set <サービス名またはサービスID> KEY=VALUE
```

### 手動デプロイの実行

```bash
render deploy <サービス名またはサービスID>
```

## 定期的なログ監視の自動化

以下のシェルスクリプトを使用して、定期的にログを確認し、エラーがあれば通知することができます：

```bash
#!/bin/bash
# check_render_logs.sh

SERVICE_NAME="hatena-bookmark-app"
LOG_DIR="./logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/render_log_${TIMESTAMP}.txt"

# ログディレクトリがなければ作成
mkdir -p $LOG_DIR

# 過去1時間のログを取得
echo "Fetching logs for $SERVICE_NAME..."
render logs $SERVICE_NAME --since 1h > $LOG_FILE

# エラーログをカウント
ERROR_COUNT=$(grep -i "error\|exception\|fail" $LOG_FILE | wc -l)

echo "Log saved to $LOG_FILE"
echo "Found $ERROR_COUNT potential errors"

# エラーが見つかった場合に通知
if [ $ERROR_COUNT -gt 0 ]; then
    echo "Errors found in logs. Please check $LOG_FILE"
    # ここに通知コマンドを追加（例：メール送信、Slack通知など）
fi
```

使用方法：

```bash
chmod +x check_render_logs.sh
./check_render_logs.sh
```

crontabに追加して定期実行することもできます：

```bash
# 1時間ごとに実行
0 * * * * /path/to/check_render_logs.sh
```

このスクリプトを使用することで、定期的にログを監視し、問題が発生した場合に迅速に対応することができます。