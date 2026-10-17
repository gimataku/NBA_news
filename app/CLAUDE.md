# CLAUDE.md

## プロジェクト概要
NBAニュース翻訳アプリ（個人利用・著作権法第30条の私的利用範囲で限定公開）
海外NBAニュースのRSSを定時取得し、Claude APIで日本語要約・カテゴリ分類して表示する。現在はフェーズ3。JWT認証付きで、Render（無料 Web Service＋Static Site）＋Neon（PostgreSQL）＋GitHub Actions（バッチ）の構成で限定公開している。

## 技術スタック
- バックエンド：Python 3.11 / FastAPI / SQLAlchemy ＋ PostgreSQL（Neon・psycopg 3）※ローカル開発の既定は SQLite / slowapi（ログインのレート制限）/ feedparser / requests
- バッチ：GitHub Actions（cron）→ `backend/run_batch_once.py`。APScheduler はローカル開発用（本番 Render は `ENABLE_SCHEDULER=false`）
- フロントエンド：React 18 / Vite / Tailwind CSS
- 外部API：Claude API（claude-haiku-4-5-20251001）/ BALLDONTLIE API / RSS
- ホスティング・監視：Render（無料プラン）/ Neon（無料枠）/ healthchecks.io（外部 cron 監視）

## ディレクトリ構成
```
NBA_news/                      # リポジトリルート（Claude Code の作業ディレクトリは app/）
├── render.yaml                # Render Blueprint（正）
├── .github/workflows/
│   └── batch.yml              # バッチ（GitHub Actions cron）
├── .env.example
├── setup.md                   # 環境構築手順
├── README.md
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
    └── CLAUDE.md              # 本ファイル（Claude Code が読むため app/ に置く）
```

## 設計書（必ず参照すること）
（パスはリポジトリルート `NBA_news/` 起点。`app/` から見ると `docs/…`）
- 要件定義書：app/docs/Requirement/requirements_p3_v0.6.md
- 基本設計書：app/docs/Basic_Design/basic_design_p3_v0.8.md
- 詳細設計書：app/docs/Detail_Design/detail_design_p3_v0.4.md
- テスト設計書：app/docs/Test_Design/test_design_p3_v0.6.md
- リスク調査書：app/docs/Risk_Report/risk_report_p3_v0.6.md
- リスク評価書：app/docs/Risk_Evaluation/risk_evaluation_p3_v0.4.md
- 計画書：app/docs/Project_Plan/project_plan_p3_v3.8.md
- 実施記録・発見事項：app/docs/Project_Plan/manufacturing_verification_log_p3.md
- フェーズ2版（`*_p2_*`）は過去の記録であり、実装の根拠にしない

## 実装上の重要な注意事項

### RSS取得
- feedparser.parse()は直接使用禁止。必ずrequests.get()でコンテンツ取得後にfeedparser.parse(response.content)へ渡す
- タイムアウトは(5, 10)（接続5秒・読み取り10秒）
- フェールオーバー順：Hoops Rumors → Hoops Wire → The Cold Wire NBA

### DB設計
- source_urlカラムはarticlesテーブルに存在しない
- APIレスポンス生成時にlinkカラムをsource_urlとして返す
  例：{"source_url": article["link"]}
- `DATABASE_URL` は**接続URL全体**。未設定時の既定は `sqlite:///nba_news.db`（ローカル）
- 本番は `postgresql+psycopg://…`（Neon の **Direct（非プール）** エンドポイント・`?sslmode=require` を残す）。Neon が提示する `postgresql://` のままだと SQLAlchemy が `psycopg2` を探して失敗する
- SQLite の絶対パスは `sqlite:////…`（スラッシュ4本）。3本は相対パスになる
- `db/migrate_p2.py` はフェーズ2の SQLite 専用。`DATABASE_URL` に `://` が含まれると `SystemExit` で終了する

### Claude API
- モデル：claude-haiku-4-5-20251001
- 1記事1リクエストで翻訳・要約・カテゴリ分類・has_scoreをまとめて処理
- has_score=Trueと判定した記事のsummary_jaにはスコア・勝敗を含めない（ネタバレ防止）
- RateLimitError（429）→ api_limit_exceeded="true"設定・当該記事をスキップ（DB保存しない）
- JSONDecodeError・バリデーション失敗 → title_ja=title_original・summary_ja=NULL・category=NULL・has_score=Falseで保存

### スケジューラ
- **本番**：GitHub Actions の cron（`.github/workflows/batch.yml`）が `python run_batch_once.py` を実行する（`init_db()` → `run_batch()` → `run_game_schedule_batch()` → 成否判定 → 任意の ping）
  - cron：`23 21,1,5,9,13,17 * * *`（UTC）＝JST 6:23・10:23・14:23・18:23・22:23・2:23
  - 手動実行は `workflow_dispatch`（Actions → Run workflow）。旧 `POST /api/fetch` は削除済み
  - GitHub の定時実行は**遅延・欠落しうる**（実測：約45〜50分遅れ・1枠の欠落あり）
- **Render（本番 Web）は `ENABLE_SCHEDULER=false`**：APScheduler も起動時バッチも動かさない。`main.py` の `_scheduler_enabled()` が `scheduler.start()`・`check_and_run_batch()`・`scheduler.shutdown()` の3箇所を分岐する。**未設定なら true**
- **ローカル開発**（既定 true）：APScheduler で10分ごとにチェックし、last_fetched_at=""（初回）または前回取得から4時間経過で実行する（この判定ロジックは従来どおり）
- 外部 cron 監視：healthchecks.io（期間4時間＋猶予5時間）。`HEALTHCHECK_PING_URL` は **GitHub Actions のみに設定し、ローカルでは設定しない**（ローカル実行の ping が本番の停止を隠すため）。未設定なら ping をスキップ

### セキュリティ
- **🔴 Claude Code は `.env` を読まない**（`cat`／`head`／`tail`／`grep`／`wc`／`od`／`xxd`／`strings`／`source`／dotenv 読み込み、およびエディタ・ファイル読み取りツールでの閲覧を含む）。**値の確認が必要な場合は Takumi様に依頼する。`.env` の内容・シークレットをチャット・ログ・文書・コミットに出力しない。** 環境変数の存在確認が必要なときも値を表示しない（キー名のみ確認する）。`.env.example` は実値を含まないため読んでよい
- （上記とは別に）アプリは実行時に APIキー等を環境変数／`.env` から読む。ハードコード禁止
- ローカル開発時はhost="127.0.0.1"で起動。Render 本番は `HOST=0.0.0.0`・CORS の許可オリジンは環境変数 `ALLOWED_ORIGINS`
- **レート制限**：`POST /api/auth/login` のみ `5/minute`（`config.LOGIN_RATE_LIMIT`）。超過は HTTP 429
  - キーは `api/limiter.py` の `get_client_ip`：①`CF-Connecting-IP` → ②`X-Forwarded-For` の**右から2番目** → ③`request.client.host`
  - 🔴 **`X-Forwarded-For` の先頭は使わない**（クライアントが偽装できる。Render は上書きせず右に追記する）。**`uvicorn.run` に `forwarded_allow_ips="*"`（`proxy_headers`）を入れ直さない**（フォールバックが偽装できる値になる）。先頭を採っていたため偽装でバイパスされた実績がある（7-A-4 の F8）
- **CORS**：`allow_methods`・`allow_headers` は `config.CORS_ALLOW_METHODS`（`GET`・`POST`・`PUT`）・`CORS_ALLOW_HEADERS`（`Authorization`・`Content-Type`）。`main.py` とテストが同じ定数を読む。`*` に戻さない。**`PUT` を落とさない**（`PUT /api/settings` がネタバレ防止トグル・チームフィルタを保存する）
- `/api/schedule` の `start_date`／`end_date` は `date` 型（`YYYY-MM-DD`）。不正値は 422
- バッチ用の GitHub Secrets は `ANTHROPIC_API_KEY`・`BALLDONTLIE_API_KEY`・`DATABASE_URL`・`HEALTHCHECK_PING_URL`。**認証系3件（`SECRET_KEY`・`USERNAME`・`USER_PASSWORD`）は登録しない**（バッチ経路は `auth` を import しない）

### ログ
- main.py起動時にos.makedirs("logs", exist_ok=True)を実行
- ログ出力先：logs/nba_news.log
- `run_batch_once.py`（GitHub Actions）はファイルログを出さず標準出力のみ。ログは Actions のジョブログで見る

### Render・運用上の注意
- `render.yaml`（リポジトリルート）は Blueprint として連携されており**正（source of truth）**。🔴 **Blueprint sync はダッシュボードの値を `render.yaml` の内容で上書きする**（プレースホルダが残ると正しい値が壊れる／`autoDeploy` 未指定は既定の On に戻りうる）。編集は最小回数にまとめる
- シークレット5件（`ANTHROPIC_API_KEY`・`BALLDONTLIE_API_KEY`・`SECRET_KEY`・`USERNAME`・`USER_PASSWORD`）と `DATABASE_URL` は `sync: false`（値はダッシュボードで入力し、ファイルに書かない）
- Auto-Deploy は On（On Commit）：push のたびにバックエンドが再デプロイされる。失敗したデプロイは捨てられ、直前の成功版が Live に残る（`healthCheckPath: /healthz`）
- 無料プランの制約：15分アクセスが無いとスピンダウン（復帰に約1分）／Render Shell は使えない／Persistent Disk なし（本番で SQLite ファイルは使わない）
- Neon 無料枠：ストレージ 1 GB／100 CU-hours／月／ネットワーク転送 5 GB／月／5分で scale-to-zero。CU-hours・転送を超えると次の請求期間までコンピュートが停止する（超過課金なし）。観測は Neon ダッシュボードの目視のみ
- `init_user()` は冪等（`count_users() > 0` なら何もしない）。**`USERNAME`／`USER_PASSWORD` を変えても、DB に保存済みのハッシュは更新されない**。本番（Neon）での資格情報の変更手順は未整備

### テスト
- `app/backend` から `pytest`。**`DATABASE_URL` を外して実行する**（PowerShell：`Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue`）
- `conftest.py` はシークレット5件と `DATABASE_URL` にダミー値を無条件代入し、`.env` を読まない（`load_dotenv` なし）。テスト用 DB は `conftest.py` 自前のエンジン（SQLite）
- 既知：`test_crud.py::test_t10_delete_old_articles` は秒境界で不安定（本番コードは正しい・別途修正予定）
- 件数は実測値で確認する（2026-10-18 時点で 138 passed）
- フロントエンド：`app/frontend` から `npm test`（vitest run）／`npm run test:cov`（カバレッジ）。テストは `src/__tests__/`。記述規約：クラス名・`▶`/`▼`・CSS でアサートしない／`getByRole`・`getByText` で取る／`data-testid` は最後の手段。`vite.config.js` に `envPrefix` を設定しない（環境変数がブラウザに配信される）
