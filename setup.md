# NBA News JP セットアップ手順

## 前提条件

- Python 3.11 以上
- Node.js 18 以上
- ANTHROPIC_API_KEY（[Anthropic Console](https://console.anthropic.com/) から取得）
- BALLDONTLIE_API_KEY（[balldontlie.io](https://www.balldontlie.io/) から取得）

本番運用には Render・Neon・GitHub・（任意）healthchecks.io のアカウントが必要です（ローカルで動かすだけなら不要）。

---

## 1. バックエンドのセットアップ

リポジトリルート（`NBA_news/`）から実行する：

```
cd app/backend
python -m venv venv
```

仮想環境を有効化する：

- **Windows**:
  ```
  venv\Scripts\activate
  ```
- **Mac / Linux**:
  ```
  source venv/bin/activate
  ```

依存パッケージをインストールする：

```
pip install -r requirements.txt
```

---

## 2. 環境変数の設定

リポジトリルート（`NBA_news/`）に `.env` を新規作成し、以下の5項目をすべて設定する：

```
ANTHROPIC_API_KEY=sk-ant-xxxxx
BALLDONTLIE_API_KEY=xxxxx
SECRET_KEY=（下記コマンドで生成した値を貼り付ける）
USERNAME=任意のログインユーザー名
USER_PASSWORD=任意のログインパスワード
```

`SECRET_KEY` は以下のコマンドで生成する（OpenSSL が必要）：

```
openssl rand -hex 32
```

> **重要**: `ANTHROPIC_API_KEY` / `BALLDONTLIE_API_KEY` / `SECRET_KEY` / `USERNAME` / `USER_PASSWORD` のいずれかが未設定または空文字の場合、
> バックエンド起動時に `RuntimeError` が発生してサービスが起動しません。

### 任意の環境変数

ローカル開発では設定不要です（既定値で動きます）。

| 変数 | 既定／用途 |
|---|---|
| `DATABASE_URL` | 接続URL全体。既定 `sqlite:///nba_news.db`（ローカル）。本番は `postgresql+psycopg://…`（Neon・Direct エンドポイント）。**値はシークレット（パスワードを含む）** |
| `ENABLE_SCHEDULER` | 既定 true。**本番（Render）は `false`**（バッチは GitHub Actions が実行） |
| `ALLOWED_ORIGINS` | CORS の許可オリジン（カンマ区切り）。既定 `http://localhost:5173` |
| `HEALTHCHECK_PING_URL` | **GitHub Actions のみに設定**。**ローカルでは設定しない**（ローカル実行の ping が本番の停止を隠すため） |
| `HOST`・`PORT` | 既定 `127.0.0.1`・`8000`（Render 本番は `HOST=0.0.0.0`） |

---

## 3. バックエンドの起動

仮想環境を有効化した状態で、`app/backend/` ディレクトリから実行する：

```
python main.py
```

起動成功時のログ出力例（ローカル既定の `ENABLE_SCHEDULER=true` の場合）：

```
INFO  DB initialized
INFO  Initial user check completed
INFO  Scheduler started
```

- `ENABLE_SCHEDULER=false` のときは `Scheduler disabled (ENABLE_SCHEDULER=false)` が出て、`Scheduler started` は出ない
- ローカル（`DATABASE_URL` 未設定）の場合、初回起動時に `app/backend/nba_news.db` が自動作成される
- `app/backend/logs/nba_news.log` にもログが書き出される
- バックエンドは `http://127.0.0.1:8000` で起動する

---

## 4. フロントエンドのセットアップ・起動

新しいターミナルを開き、リポジトリルートから実行する：

```
cd app/frontend
npm install
npm run dev
```

- フロントエンドは `http://localhost:5173` で起動する
- `/api` へのリクエストはバックエンド（`http://127.0.0.1:8000`）へ自動プロキシされる

---

## 5. 動作確認

1. バックエンドとフロントエンドの両方を起動した状態で、ブラウザで `http://localhost:5173` を開く
2. ログインフォームが表示されることを確認する
3. 手順 2 で設定した `USERNAME` / `USER_PASSWORD` でログインする
4. ニュース一覧画面に遷移すれば正常に動作している

---

## 6. テストの実行

`app/backend/` ディレクトリから実行する。**`DATABASE_URL` が設定されていない状態で実行すること**（テストは `conftest.py` 自前の SQLite を使い、`.env` は読まない）：

- **Windows（PowerShell）**:
  ```
  Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue
  pytest
  ```
- **Mac / Linux**:
  ```
  unset DATABASE_URL
  pytest
  ```

2026-10-18 時点で 138 passed。`test_crud.py::test_t10_delete_old_articles` は秒境界で失敗することがある（既知・本番コードは正しい）。

### フロントエンドのテスト

`app/frontend/` ディレクトリから実行する（初回は `npm install` が必要）：

```
npm test          # テスト実行（vitest）
npm run test:cov  # カバレッジ付き（coverage/ に出力。Git 管理外）
```

テストは `app/frontend/src/__tests__/` に置く。記述規約：クラス名・`▶`/`▼` の記号・CSS をアサートしない／要素は `getByRole`・`getByText` で取る／`data-testid` は最後の手段。

---

## トラブルシューティング

### RuntimeError: SECRET_KEY が未設定です

リポジトリルートの `.env` に `SECRET_KEY=` の行が存在するか確認してください。
値が空文字の場合も同じエラーになります。`openssl rand -hex 32` で生成した値を設定してください。

### RuntimeError: USERNAME / USER_PASSWORD が未設定です

リポジトリルートの `.env` に `USERNAME=` と `USER_PASSWORD=` が両方設定されているか確認してください。

### RuntimeError: ANTHROPIC_API_KEY / BALLDONTLIE_API_KEY が未設定です

リポジトリルートの `.env` に `ANTHROPIC_API_KEY=` と `BALLDONTLIE_API_KEY=` が両方設定されているか確認してください。

### ModuleNotFoundError: No module named 'psycopg' / 'psycopg2'

- `psycopg`：依存パッケージが不足しています。`pip install -r requirements.txt` を実行してください。
- `psycopg2`：`DATABASE_URL` のスキームが `postgresql://` のままです。`postgresql+psycopg://` に書き換えてください。

### pytest が collection で失敗する

`DATABASE_URL` に接続URLが残っている可能性があります。外してから再実行してください（「6. テストの実行」参照）。

### ログインが 429 になる

ログイン試行のレート制限（1分あたり5回）を超えています。1分ほど待ってから再試行してください。

### （本番）初回アクセスが遅い

Render の無料プランは15分アクセスが無いとスピンダウンします。復帰に約1分かかります。

### ポート 8000 が使用中

別プロセスがポート 8000 を使用しています。以下でプロセスを確認して終了してください：

- **Windows**: `netstat -ano | findstr :8000` でPIDを確認 → `taskkill /PID <PID> /F`
- **Mac / Linux**: `lsof -i :8000` でPIDを確認 → `kill <PID>`

### ポート 5173 が使用中

Vite は空きポートを自動的に探して起動します（例: 5174, 5175...）。
ターミナルに表示された URL を使用してください。

### ログインできない

- バックエンドが起動していることを確認してください（`http://127.0.0.1:8000/docs` にアクセスできるか）
- `.env` の `USERNAME` / `USER_PASSWORD` に設定した値を正確に入力しているか確認してください
- `USERNAME` / `USER_PASSWORD` を変更しても、保存済みのハッシュは更新されません（`init_user()` は冪等）。
- ローカル（SQLite）の場合に限り、DB を削除して再起動すると初回ユーザーが再作成されます：
  - **Windows**: `del app\backend\nba_news.db`
  - **Mac / Linux**: `rm app/backend/nba_news.db`
  - その後 `python main.py` で再起動
- 本番（Neon）での資格情報の変更手順は未整備です（Render の無料プランでは Shell が使えません）。変更が必要なときは別途手順を整えます。

---

## Render 本番運用手順

> **前提**: ローカル開発が正常に動作していること（手順1〜5 が完了していること）。

### Render 構成概要

本アプリはリポジトリルート（`NBA_news/`）の `render.yaml` で2サービス構成を定義している：

| サービス | 種別 | 役割 |
|---|---|---|
| `nba-news-backend` | Web Service（無料プラン） | Python/FastAPI バックエンドのみ（バッチは動かさない。`ENABLE_SCHEDULER=false`） |
| `nba-news-frontend` | Static Site（無料） | React フロントエンド |

Render 以外の構成要素：

| 構成要素 | 役割 |
|---|---|
| Neon（PostgreSQL・無料） | データベース |
| GitHub Actions | バッチ（`.github/workflows/batch.yml` が `run_batch_once.py` を実行） |
| healthchecks.io（任意） | 外部 cron 監視 |

### 手順 A：GitHubリポジトリとRenderの連携

1. [Render ダッシュボード](https://dashboard.render.com/) にログインする
2. 「New +」→「Blueprint」を選択し、このリポジトリを連携する
3. Render が `render.yaml` を自動検出し、2サービスの構成を表示する
4. 確認後「Apply」でサービスを作成する

> **重要**: `render.yaml` が正（source of truth）です。**Blueprint sync はダッシュボードの値を `render.yaml` の内容で上書きします**。ダッシュボードだけで値を変えても、次の sync で戻ります。

### 手順 B：シークレット環境変数の手動入力

`render.yaml` にはセキュリティ上 `sync: false` として値を記載していない。以下5項目を Render ダッシュボードの **`nba-news-backend` サービス → Environment → Environment Variables** で手動入力すること：

| 変数名 | 値の取得方法 |
|---|---|
| `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com/) |
| `BALLDONTLIE_API_KEY` | [balldontlie.io](https://www.balldontlie.io/) |
| `SECRET_KEY` | `openssl rand -hex 32` で生成 |
| `USERNAME` | 任意のログインユーザー名 |
| `USER_PASSWORD` | 任意のログインパスワード |

`DATABASE_URL` も `sync: false` です。値は手順 D で用意し、ダッシュボードで入力します。

> **重要**: 5項目のいずれかが未設定または空文字の場合、バックエンドは起動時に `RuntimeError` を発生させ起動しません。

### 手順 C：URL の管理

現在は実 URL が `render.yaml` に設定済みです。URL が変わる場合は **`render.yaml` を編集して push** してください（ダッシュボードだけの変更は次の sync で上書きされます）。**`render.yaml` に `YOUR_` 等のプレースホルダを残して push しないこと。**

- **バックエンドの `ALLOWED_ORIGINS`**：フロントエンドの URL（例: `https://nba-news-frontend.onrender.com`）
- **フロントエンドの `VITE_API_BASE_URL`**：バックエンドの URL（例: `https://nba-news-backend.onrender.com`）  
  変更後は **Manual Deploy** でフロントエンドを再ビルドすること（ビルド時環境変数のため）。

### 手順 D：Neon の準備

1. Neon でプロジェクトを作成する（Free プラン）
2. 接続文字列は **Direct（Connection pooling をオフ）** のものを取得する
3. スキームを **`postgresql://` → `postgresql+psycopg://`** に書き換える（`?sslmode=require` は残す）。**入力欄の中で書き換え、チャット・Git・メモ帳に出さないこと**
4. Render のダッシュボードで `nba-news-backend` の `DATABASE_URL` に設定する
5. GitHub Secrets に登録する（手順 E′）

### 手順 E′：GitHub Actions バッチ

1. GitHub リポジトリの **Settings → Secrets and variables → Actions** に以下を登録する：
   - `ANTHROPIC_API_KEY`
   - `BALLDONTLIE_API_KEY`
   - `DATABASE_URL`（Neon。手順 D と同じ値）
   - `HEALTHCHECK_PING_URL`（外部 cron 監視を使う場合のみ）
2. **`SECRET_KEY`・`USERNAME`・`USER_PASSWORD` は登録しない**（バッチ経路は認証を使わない）
3. 定時実行：cron `23 21,1,5,9,13,17 * * *`（UTC）＝JST 6:23・10:23・14:23・18:23・22:23・2:23。**GitHub の定時実行は遅延・欠落しうる**（実測：約45〜50分遅れ・1枠の欠落あり）
4. 手動実行：Actions → NBA News Batch → Run workflow
5. **初回は Neon が空なので全記事が翻訳され、Claude API の費用が発生する**
6. バッチのログはファイルに出ず、Actions のジョブログで見る

### 外部 cron 監視（任意）

healthchecks.io（Hobbyist・無料）で、期間4時間＋猶予5時間（9時間 ping が来なければ通知）のチェックを作成し、ping URL を GitHub Secrets の `HEALTHCHECK_PING_URL` に登録する。ping URL は秘密として扱う。**ローカルでは `HEALTHCHECK_PING_URL` を設定しない**（未設定なら ping はスキップされる）。

### 手順 E：デプロイ後の動作確認

1. **ヘルスチェック確認**  
   バックエンドURL + `/healthz` にアクセスし `{"status":"ok"}` が返ることを確認する  
   例: `https://nba-news-backend.onrender.com/healthz`

2. **ログイン確認**  
   フロントエンドURL（例: `https://nba-news-frontend.onrender.com`）を開き、手順Bで設定した `USERNAME` / `USER_PASSWORD` でログインできることを確認する

3. **記事取得確認**  
   ログイン後、ニュース一覧画面が表示されること（GitHub Actions のバッチが一度実行されるまで記事は0件の場合あり）を確認する

### 運用上の注意

- **Auto-Deploy は On（On Commit）**：push のたびにバックエンドが再デプロイされる。失敗したデプロイは捨てられ、直前の成功版が Live に残る（`healthCheckPath: /healthz`）
- **`render.yaml` の編集は最小回数にまとめる**（sync がダッシュボードの値を上書きするため）
- **無料プランの制約**：15分アクセスが無いとスピンダウン（復帰に約1分）／Render Shell は使えない／Persistent Disk なし
- **Neon 無料枠**：ストレージ 1 GB／100 CU-hours／月／ネットワーク転送 5 GB／月。CU-hours・転送を超えると次の請求期間までコンピュートが停止する（超過課金なし）。使用量は Neon ダッシュボードで目視確認する
- 週次チェックリストは 7-B で整備する
