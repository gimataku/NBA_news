# NBA News JP

海外NBAニュースのRSSを定期取得し、Claude APIで日本語に要約・カテゴリ分類してブラウザで閲覧できる、個人利用の限定公開アプリです（ローカル実行も可能）。

---

## 主な機能

- **RSS自動取得**：Hoops Rumors / Hoops Wire / The Cold Wire NBA を4時間ごとに取得（フェールオーバー対応。本番は GitHub Actions の cron）
- **AI翻訳・要約**：Claude API（claude-haiku-4-5-20251001）で英語記事を日本語タイトル・800〜1200字要約に変換
- **カテゴリ分類**：`trade_fa`（トレード/FA）/ `draft`（ドラフト）/ `injury`（けが人）/ `column`（コラム）の4分類に自動分類。重複記事（`is_duplicate=True`）は全タブで非表示
- **チームフィルタ**：San Antonio Spurs 関連記事のみを絞り込み表示
- **ネタバレ防止**：試合スコア・勝敗を含む記事（`has_score=True`）を折りたたみ表示（全カテゴリ対象）
- **試合日程取得**：BALLDONTLIE API から試合日程・スコアを取得し専用タブで表示
- **JWT認証**：ログイン必須（ユーザー名・パスワード）。トークンはブラウザのメモリにのみ保持（ローカルストレージ不使用）。ログインはレート制限あり（1分あたり5回・超過は HTTP 429）
- **データ自動削除**：30日経過した記事を自動削除

---

## 技術スタック

| レイヤー | 使用技術 |
|---|---|
| バックエンド | Python 3.11 / FastAPI / SQLAlchemy / PostgreSQL（Neon）※ローカル既定は SQLite / slowapi / APScheduler（ローカル開発用） |
| フロントエンド | React 18 / Vite / Tailwind CSS |
| 外部API | Claude API / BALLDONTLIE API / RSS |
| バッチ | GitHub Actions（cron）→ `backend/run_batch_once.py` |
| ホスティング | Render（無料プラン：Web Service＋Static Site）/ Neon（無料枠） |
| 監視 | healthchecks.io（外部 cron 監視） |

---

## ディレクトリ構成

```
NBA_news/
├── render.yaml                # Render Blueprint（正）※app/ の外
├── .github/workflows/
│   └── batch.yml              # バッチ（GitHub Actions cron）※app/ の外
└── app/
    ├── backend/
    │   ├── main.py            # FastAPI エントリーポイント
    │   ├── scheduler.py       # バッチ処理・APScheduler 設定（APScheduler はローカル開発用）
    │   ├── run_batch_once.py  # 1回限りのバッチ実行（GitHub Actions から起動）
    │   ├── monitor.py         # 稼働状況の確認スクリプト（手動実行）
    │   ├── config.py          # 環境変数・定数
    │   ├── requirements.txt
    │   ├── fetcher/
    │   │   ├── rss.py         # RSS取得
    │   │   └── score.py       # BALLDONTLIE スコア取得
    │   ├── processor/
    │   │   ├── claude_client.py  # Claude API 翻訳・分類
    │   │   ├── dedup.py          # 重複排除（Levenshtein距離80%閾値）
    │   │   └── filter.py         # Spurs 関連フィルタ
    │   ├── auth/
    │   │   ├── jwt.py            # JWT認証
    │   │   └── users.py          # ユーザー管理
    │   ├── db/
    │   │   ├── models.py      # テーブル定義・DB初期化
    │   │   ├── crud.py        # CRUD 操作
    │   │   └── migrate_p2.py  # フェーズ2の SQLite 専用マイグレーション
    │   ├── api/
    │   │   ├── routes.py      # FastAPI ルーティング
    │   │   └── limiter.py     # ログインのレート制限（キー関数 get_client_ip）
    │   ├── tests/             # pytest（conftest.py ほか）
    │   └── logs/
    │       └── nba_news.log   # main.py 起動時に作成
    ├── frontend/
    │   └── src/
    │       ├── App.jsx
    │       ├── components/    # LoginForm / CategoryTabs / FilterBar / NewsCard / GameSchedule / SpoilerOverlay
    │       └── hooks/         # useAuth / useNews
    ├── docs/                  # ドキュメント類
    │   ├── Basic_Design/      # 基本設計書
    │   ├── Detail_Design/     # 詳細設計書
    │   ├── Project_Plan/      # プロジェクト計画書・実装指示・実施記録
    │   ├── Requirement/       # 要件定義書
    │   ├── Retrospective/     # 振り返り
    │   ├── Risk_Evaluation/   # リスク評価書
    │   ├── Risk_Report/       # リスク調査書
    │   ├── Test_Design/       # テスト設計書
    │   └── Trial/             # トライアル運用関連
    ├── .env.example
    ├── setup.md               # 環境構築手順
    ├── README.md
    └── CLAUDE.md
```

---

## セットアップ

詳細な手順は [setup.md](./setup.md) を参照してください。以下は概要です。

### 1. 前提条件

- Python 3.11 以上
- Node.js 18 以上

### 2. .env の準備

```bash
cp .env.example .env
# .env を開き以下の変数を記入
# ANTHROPIC_API_KEY / BALLDONTLIE_API_KEY / SECRET_KEY（任意の長い文字列）/ USERNAME / USER_PASSWORD
```

### 3. バックエンド依存パッケージのインストール

```bash
pip install -r backend/requirements.txt
```

### 4. フロントエンド依存パッケージのインストール

```bash
cd frontend && npm install
```

---

## 起動方法

バックエンドとフロントエンドをそれぞれ別ターミナルで起動します。

```bash
# バックエンド（ポート 8000）
cd backend && python main.py

# フロントエンド（ポート 5173）
cd frontend && npm run dev
```

ブラウザで `http://localhost:5173` を開くと画面が表示されます。

ローカル開発（`ENABLE_SCHEDULER` 既定 true）では、起動後に初回バッチが自動実行されRSSが取得されます。その後は4時間ごとに自動更新されます。本番（Render）ではバッチを動かさず、GitHub Actions がバッチを実行します。

---

## API エンドポイント

| メソッド | パス | 説明 |
|---|---|---|
| POST | `/api/auth/login` | ログイン（ユーザー名・パスワード → JWTトークン発行）。1分あたり5回を超えると 429 |
| GET | `/api/news` | 記事一覧取得（要認証。category / spurs_only / limit / offset でフィルタ可） |
| GET | `/api/schedule` | 試合日程一覧取得（要認証。`start_date`・`end_date` は `YYYY-MM-DD`。不正値は 422） |
| GET | `/api/status` | 最終取得日時・使用ソース・API制限状態・`metrics`（運用指標）（要認証） |
| GET | `/api/settings` | 設定値取得（要認証） |
| PUT | `/api/settings` | 設定値の更新（要認証） |
| GET | `/healthz` | ヘルスチェック（認証不要） |

---

## 環境変数

`.env.example` を参考に `.env` を作成してください。

| 変数名 | 説明 | 取得先 |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API キー | https://console.anthropic.com/ |
| `BALLDONTLIE_API_KEY` | BALLDONTLIE API キー | https://app.balldontlie.io/ |
| `SECRET_KEY` | JWT署名用シークレット（任意の長い文字列） | 自分で生成（例：`openssl rand -hex 32`） |
| `USERNAME` | ログインユーザー名 | 自分で設定 |
| `USER_PASSWORD` | ログインパスワード | 自分で設定 |

任意の環境変数（`DATABASE_URL`・`ENABLE_SCHEDULER`・`ALLOWED_ORIGINS`・`HEALTHCHECK_PING_URL`・`HOST`・`PORT`）は [setup.md の「任意の環境変数」](./setup.md#任意の環境変数) を参照してください。

---

## ログ

```
logs/nba_news.log
```

ローカル／Render の Web サービスのログです。バッチ実行・RSS取得・Claude API 呼び出し・エラーが記録されます。

バッチ（GitHub Actions の `run_batch_once.py`）はファイルログを出さず標準出力のみです。Actions のジョブログで確認してください。

---

## ライセンス

個人利用のみを目的としたプロジェクトです。
