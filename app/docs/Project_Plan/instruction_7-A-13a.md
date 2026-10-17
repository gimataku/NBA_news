# 実装指示 7-A-13a：プロジェクトドキュメント追従更新（第1弾：移行・セキュリティ・運用の反映）

作成日：2026-10-17 ／ 主担当：Claude Code（文書の更新）→ Takumi様（確認・commit）
対象：`CLAUDE.md`・`setup.md`・`README.md`（いずれも `app/` 直下）
由来：計画書 手順7「必須サブ手順：プロジェクトドキュメント追従更新」（振り返り3-2）。**本文書は 7-A-13 の前半（13a）**。後半（13b）は 7-A-6〜7-A-8 の完了後（§7）。

> **なぜ先に行うか**: `CLAUDE.md` は Claude Code が実装前に読む指示書である。**現状は「cron 方式は使用しない」「APScheduler で10分ごとにチェック」「SQLite3」など、移行後の実態と正反対の記述が残っている**。このままだと、誤った前提で実装・修正される。開幕（2026-10-20）前に是正する。

---

## 0. 作業範囲と禁止事項

- **変更するのは文書3ファイルのみ**（`CLAUDE.md`・`setup.md`・`README.md`）。**コード・テスト・`render.yaml`・`.env.example` は変更しない。**
- 🔴 **`.env` を読まない**（`cat`／`head`／`tail`／`grep`／`wc`／`od`／`xxd`／`strings`／`source`／dotenv 読み込みのいずれも）。**シークレット・接続文字列・API キー・実在のパスワードを文書に書かない。** 例示は `xxxxx`・`ユーザー名` 等のダミーのみ。
- **事実のみを書く。** 本書に書かれていない事実を推測で足さない。**コードで確認できるもの（`config.py`・`main.py`・`scheduler.py`・`run_batch_once.py`・`requirements.txt`・`api/limiter.py`・ディレクトリ構成）は、書く前に必ず実物で確認する**。`render.yaml`・`.github/workflows/batch.yml` はリポジトリルート（`app/` の外）にあり、Claude Code からは読めない。**これらに関する記述は本書の内容（Takumi様確認済み・2026-10-13〜17）をそのまま使う。**
- **資格情報の変更手順は書かない**（未整備。§3-4 の指定文言のみ）。
- 既存の文体（です・ます／常体の混在はそのまま。**見出し構成は大きく変えない**）。

---

## 1. 確認済みの事実（本書が根拠。文書に書く内容の出典）

| # | 事実 | 出典 |
|---|---|---|
| F1 | 本番構成：Render **Web Service（無料プラン）**＋**Static Site**／DB は **Neon（PostgreSQL・psycopg 3）**／バッチは **GitHub Actions（cron）** | 7-A-10 完了（2026-10-14） |
| F2 | `DATABASE_URL` は**接続URL全体**。本番は `postgresql+psycopg://…`（Neon の **Direct（非プール）** エンドポイント・`?sslmode=require` を残す）。Neon が提示する `postgresql://` のままだと SQLAlchemy は `psycopg2` を探して失敗する。**ローカル既定は `sqlite:///nba_news.db`**。SQLite の絶対パスは `sqlite:////…`（スラッシュ4本）で、3本は相対パスになる | `db/models.py`・7-A-10 |
| F3 | `db/migrate_p2.py` は**フェーズ2の SQLite 専用**。`DATABASE_URL` に `://` が含まれると `SystemExit` で終了する（ガード） | 7-A-9／前提B |
| F4 | バッチ：`backend/run_batch_once.py`（`init_db()` → `run_batch()` → `run_game_schedule_batch()` → 成否判定 → 任意の ping）。**ファイルログは出さず標準出力のみ**。GitHub Actions：`.github/workflows/batch.yml`（`NBA_news/.github/workflows/`）。cron は **`23 21,1,5,9,13,17 * * *`（UTC）＝JST 6:23・10:23・14:23・18:23・22:23・2:23**。手動実行は `workflow_dispatch`（旧 `POST /api/fetch` の代替。**`/api/fetch` は削除済み**）。**GitHub の定時実行は遅延・欠落しうる**（実測：約45〜50分遅れ・10:00 の枠が1回欠落） | 7-A-9・7-A-10・7-A-11・7-A-12 |
| F5 | GitHub Secrets は **`ANTHROPIC_API_KEY`・`BALLDONTLIE_API_KEY`・`DATABASE_URL`（Neon）・`HEALTHCHECK_PING_URL`**。**認証系3件（`SECRET_KEY`・`USERNAME`・`USER_PASSWORD`）は登録しない**（バッチ経路は `auth` を import しない） | 7-A-1・7-A-10 |
| F6 | Render 側は **`ENABLE_SCHEDULER=false`**。`main.py` の `_scheduler_enabled()`（`os.getenv("ENABLE_SCHEDULER", "true").lower() != "false"`）が、`scheduler.start()`・`check_and_run_batch()`・`scheduler.shutdown()` の3箇所を分岐する。**未設定なら true（ローカル開発では従来どおり APScheduler が動く）** | 7-A-10c |
| F7 | 外部 cron 監視：**healthchecks.io**（Hobbyist・無料）。期間4時間＋猶予5時間（9時間 ping が来なければ通知）。`HEALTHCHECK_PING_URL` は **GitHub Actions 上でのみ設定**し、**ローカルでは設定しない**（ローカル実行の ping が本番の停止を隠すため）。未設定なら ping をスキップ | 7-A-12 |
| F8 | レート制限：`POST /api/auth/login` のみ `5/minute`（`config.LOGIN_RATE_LIMIT`）。**キーは `api/limiter.py` の `get_client_ip`**：①`CF-Connecting-IP` → ②`X-Forwarded-For` の**右から2番目** → ③`request.client.host`。🔴**`X-Forwarded-For` の先頭はクライアントが偽装できるため使わない**（Render は上書きせず追記する）。**`uvicorn.run` に `forwarded_allow_ips="*"` を入れ直してはならない**（フォールバックが偽装できる値になる）。超過時は HTTP 429、UI は「ログインの試行が多すぎます。1分ほど待ってから再試行してください。」 | 7-A-4・7-A-4c（F8） |
| F9 | CORS：`allow_methods`＝`["GET","POST","PUT"]`・`allow_headers`＝`["Authorization","Content-Type"]`（`config.CORS_ALLOW_METHODS`・`CORS_ALLOW_HEADERS`。**`main.py` とテストの双方が同じ定数を読む**）。**`PUT` を落とさない**（`PUT /api/settings` がネタバレ防止トグル・チームフィルタを保存する）。`allow_origins` は環境変数 `ALLOWED_ORIGINS` | 7-A-5 |
| F10 | `/api/schedule` の `start_date`／`end_date` は `date` 型（`YYYY-MM-DD`）。不正値は 422。`/api/status` の応答に `metrics`（`total_articles`・`articles_last_7d`・`by_category_7d`・`duplicate_count`・`fallback_history_7d`）が含まれる（`config.METRICS_WINDOW_DAYS=7`） | 7-A-3・7-A-5 |
| F11 | `render.yaml`（リポジトリルート）は **Blueprint として連携**され、**正（source of truth）**。🔴**Blueprint sync は、ダッシュボードの値を `render.yaml` の内容で上書きする**（プレースホルダが残ると正しい値が壊れる／`autoDeploy` 未指定は既定の On に戻りうる）。シークレット5件（`ANTHROPIC_API_KEY`・`BALLDONTLIE_API_KEY`・`SECRET_KEY`・`USERNAME`・`USER_PASSWORD`）と `DATABASE_URL` は **`sync: false`**（値はダッシュボードで入力。ファイルに書かない）。`render.yaml` の編集は**最小回数にまとめる**。**Auto-Deploy は On（On Commit）**：push のたびにバックエンドが再デプロイされる。失敗したデプロイは捨てられ直前の成功版が Live に残る（`healthCheckPath: /healthz`） | F4・F7・7-A-10 |
| F12 | **無料プランの制約**：15分アクセスが無いとスピンダウン（復帰に約1分）／**Render Shell は使えない**／Persistent Disk なし（`disk:` は削除済み。SQLite ファイルは本番では使わない） | 7-A-10 |
| F13 | Neon 無料枠：ストレージ 1 GB／**100 CU-hours／月**／**ネットワーク転送 5 GB／月**／5分で scale-to-zero。**CU-hours・転送の超過は次の請求期間までコンピュート停止**（超過課金なし）。観測手段は Neon ダッシュボードの目視のみ | 7-A-10 |
| F14 | テスト：`pytest` は **`DATABASE_URL` を外した状態で実行**する。`conftest.py` はシークレット5件と `DATABASE_URL` のダミー値を**無条件代入**し、`.env` を読まない（`load_dotenv` なし）。テスト用 DB は SQLite（`conftest.py` 自前のエンジン）。**既知：`test_crud.py::test_t10_delete_old_articles` は秒境界で不安定**（本番コードは正しい・別途修正予定）。件数は実測値を確認して書く（現在 133 passed が目安） | 7-A-4・7-A-5 |
| F15 | **`init_user()` は冪等**（`count_users() > 0` なら何もしない）。**環境変数 `USERNAME`／`USER_PASSWORD` を変えても、DB に保存済みのハッシュは更新されない** | 7-A-3（F4 の教訓） |
| F16 | **設計書の最新版**：要件定義書 `requirements_p3_v0.6.md`／基本設計書 `basic_design_p3_v0.8.md`／詳細設計書 `detail_design_p3_v0.4.md`／テスト設計書 `test_design_p3_v0.6.md`／リスク調査書 `risk_report_p3_v0.6.md`／リスク評価書 `risk_evaluation_p3_v0.4.md`／計画書 `project_plan_p3_v3.8.md`（**`docs/` 配下の実ファイルで版を確認してから書く**。上記と異なる最新版があればそちらを書き、差異を報告する） | `docs/` |

---

## 2. `CLAUDE.md` の変更

**見出しの構成は維持し、各節の記述を F1〜F16 に合わせて更新する。** 現状の節と変更内容：

| 節 | 現状の記述（要旨） | 変更内容 |
|---|---|---|
| プロジェクト概要 | 「フェーズ2でJWT認証を追加しRender経由で限定公開する」 | 「**現在はフェーズ3。JWT認証付きで、Render（無料 Web Service＋Static Site）＋Neon（PostgreSQL）＋GitHub Actions（バッチ）の構成で限定公開している**」に更新（F1） |
| 技術スタック | `Python 3.11 / FastAPI / SQLite3 / APScheduler / feedparser / requests` | **SQLite3 → SQLAlchemy ＋ PostgreSQL（Neon・psycopg 3）。ローカル開発の既定は SQLite**。`slowapi`（ログインのレート制限）を追加。**バッチ：GitHub Actions（cron）→ `run_batch_once.py`。APScheduler はローカル開発用（本番は `ENABLE_SCHEDULER=false`）**。ホスティング：Render（無料プラン）・Neon・healthchecks.io を追記（F1・F6・F7） |
| ディレクトリ構成 | `app/` 配下のツリー | **実物を `ls` で確認して**、不足を追記する：`backend/run_batch_once.py`・`backend/api/limiter.py`・`backend/db/migrate_p2.py`・`backend/tests/`・`frontend/src/hooks/`。さらに**リポジトリルート（`app/` の外）**に `render.yaml`・`.github/workflows/batch.yml` があることを**注記として**書く（ツリーの `NBA_news/` 直下）。`docs/` 配下の実在するフォルダ名（`Risk_Evaluation/` 等）も実物に合わせる |
| 設計書（必ず参照すること） | `detail_design_p2_v0.4.md`／`basic_design_p2_v0.5.md`／`requirements_p2_v0.12.md` | **フェーズ3版に更新**（F16）。**フェーズ2版は過去の記録であり、実装の根拠にしない**旨を1行添える。`docs/Project_Plan/manufacturing_verification_log_p3.md`（各サブ手順の実施記録・発見事項）も参照先に加える |
| RSS取得／Claude API | — | **変更しない** |
| DB設計 | `source_url` カラムは存在しない／`link` を `source_url` として返す | 既存2項目は**維持**。**次を追加**（F2・F3）：`DATABASE_URL` は接続URL全体であること／本番は `postgresql+psycopg://` で Neon の Direct エンドポイント／`postgresql://` は不可／SQLite 絶対パスのスラッシュ4本／`migrate_p2.py` は SQLite 専用 |
| スケジューラ | 「APSchedulerで10分ごとにチェック」「last_fetched_at=""（初回）または前回取得から4時間経過で実行」「**cron方式は使用しない**」 | 🔴**全面的に書き換える**（F4・F6・F7）：①**本番**＝GitHub Actions の cron（`.github/workflows/batch.yml`）が `python run_batch_once.py` を実行。cron 式・JST 対応・`workflow_dispatch`・**遅延・欠落しうる**ことを書く。②**Render（本番 Web）は `ENABLE_SCHEDULER=false`**：スケジューラも起動時バッチも動かさない（`main.py` の `_scheduler_enabled()` が3箇所を分岐。**未設定なら true**）。③**ローカル開発**は既定 true で APScheduler が10分ごとにチェックし、`last_fetched_at=""`（初回）または前回取得から4時間経過で実行する（**この判定ロジックは従来どおり**）。④外部 cron 監視（healthchecks.io・4h＋5h・`HEALTHCHECK_PING_URL` は GitHub Actions のみ・ローカルでは設定しない）。⑤**「cron方式は使用しない」の記述は削除**する |
| セキュリティ | APIキーは `.env` から／`host="127.0.0.1"`／「Render本番運用時はJWT認証を前提に…（7-J-2で対応）」 | 既存の `.env`・ハードコード禁止は**維持**。「7-J-2で対応」は**対応済みの旧記述なので現状に更新**（Render 本番は `HOST=0.0.0.0`・`ALLOWED_ORIGINS` は環境変数）。**次を追加**：①**レート制限（F8）**：ログインのみ `5/minute`・キーの決め方・**`X-Forwarded-For` の先頭を使わない**・**`forwarded_allow_ips="*"` を入れ直さない**（理由を1行：偽装でバイパスされた実績＝F8）。②**CORS（F9）**：`*` に戻さない・`PUT` を落とさない・定数は `config.py`。③`/api/schedule` の日付検証（F10）。④バッチ側 GitHub Secrets に認証系3件を登録しない（F5）。⑤🔴**【必須・Takumi様決定 2026-10-17】`.env` を読まないルールを明記する**：「**Claude Code は `.env` を読まない**（`cat`／`head`／`tail`／`grep`／`wc`／`od`／`xxd`／`strings`／`source`／dotenv 読み込み、およびエディタ・ファイル読み取りツールでの閲覧を含む）。**値の確認が必要な場合は Takumi様に依頼する**。**`.env` の内容・シークレットをチャット・ログ・文書・コミットに出力しない**。環境変数の**存在確認が必要なときも値を表示しない**（例：キー名のみ確認する）」を、現行の「APIキーは.envから読む」（アプリが読む）と**区別して**書く（アプリの実行時の読み込みと、Claude Code の閲覧は別）。位置は「セキュリティ」節の冒頭付近で、見落とされない書き方（太字）にする。**`.env.example` は読んでよい**（実値を含まないため）旨も添える |
| ログ | `main.py` 起動時に `logs` を作成／ログ出力先 `logs/nba_news.log` | 既存を維持し、**「`run_batch_once.py`（GitHub Actions）はファイルログを出さず標準出力のみ。ログは Actions のジョブログで見る」**を追加（F4） |
| **新設：Render／運用の注意** | （無い） | **新しい節「Render・運用上の注意」を追加**（F11〜F13）：Blueprint と `render.yaml` の扱い（**sync がダッシュボードの値を上書きする**・シークレットと `DATABASE_URL` は `sync: false`・編集は最小回数に）／Auto-Deploy On（push のたびに再デプロイ・失敗は Live を壊さない）／無料プランの制約（スピンダウン・Shell 不可・ディスクなし）／Neon 無料枠（CU-hours・転送・超過時の停止）／**`init_user()` の冪等性（F15）**。**資格情報の変更手順は書かない**（§3-4 の文言のみ） |
| **新設：テスト** | （無い） | **新しい節「テスト」を追加**（F14）：`pytest` の実行方法（`app/backend` から・**`DATABASE_URL` を外す**）・`conftest.py` の方針（ダミー値の無条件代入・`.env` を読まない・SQLite の自前エンジン）・既知の不安定なテスト（`test_t10`）・件数は実測値 |

> `CLAUDE.md` は**簡潔さも価値**である。F1〜F16 のすべてを逐語で写すのではなく、**「実装者が間違えやすい点」を優先して**短く書く。特に **F8（`X-Forwarded-For`）・F11（sync の上書き）・F6（`ENABLE_SCHEDULER`）・F2（`DATABASE_URL`）**は必ず入れる。

---

## 3. `setup.md` の変更

### 3-1. 前提条件・環境変数（§1〜§2）

- 前提条件に、**本番運用には Render・Neon・GitHub・（任意）healthchecks.io のアカウントが必要**であること（**ローカルだけなら不要**）を1文追記。
- 「2. 環境変数の設定」の既存5項目（`ANTHROPIC_API_KEY`・`BALLDONTLIE_API_KEY`・`SECRET_KEY`・`USERNAME`・`USER_PASSWORD`）は**維持**。その下に**任意の環境変数の表**を追加（F2・F4・F6・F7・F9）：

  | 変数 | 既定／用途 |
  |---|---|
  | `DATABASE_URL` | 接続URL全体。既定 `sqlite:///nba_news.db`（ローカル）。本番は `postgresql+psycopg://…`（Neon・Direct）。**値はシークレット（パスワードを含む）** |
  | `ENABLE_SCHEDULER` | 既定 true。**本番（Render）は `false`**（バッチは GitHub Actions が実行） |
  | `ALLOWED_ORIGINS` | CORS の許可オリジン（カンマ区切り）。既定 `http://localhost:5173` |
  | `HEALTHCHECK_PING_URL` | **GitHub Actions のみに設定**。**ローカルでは設定しない** |
  | `HOST`・`PORT` | 既定 `127.0.0.1`・`8000`（Render 本番は `HOST=0.0.0.0`） |

  - **実際の既定値は `config.py`・`main.py` で確認してから書く**（上表と食い違えば実物に合わせ、報告する）。
- 既存の注記（`SECRET_KEY`／`USERNAME`／`USER_PASSWORD` が未設定だと `RuntimeError`）は維持。**さらに、`ANTHROPIC_API_KEY`／`BALLDONTLIE_API_KEY` が未設定でも `RuntimeError` になる**ことを加える（7-A-1 で `config.py` に移した）。

### 3-2. 起動（§3）・動作確認（§5）

- 起動成功時のログ例は維持（`Scheduler started` はローカル既定 `ENABLE_SCHEDULER=true` の場合）。**「`ENABLE_SCHEDULER=false` のときは `Scheduler disabled (ENABLE_SCHEDULER=false)` が出て、`Scheduler started` は出ない」**を追記（F6）。
- 「初回起動時に `nba_news.db` が自動作成される」は**ローカル（`DATABASE_URL` 未設定）の場合**と明記する。

### 3-3. テストの実行（新設）

「5. 動作確認」の後に**「6. テストの実行」**を新設（F14）：`app/backend` から `pytest`。**`DATABASE_URL` が設定されていないこと**（`Remove-Item Env:\DATABASE_URL`／`unset DATABASE_URL`）を明記。件数は実測値。**フロントエンドのテスト（`npm test`）はテスト基盤（7-A-8）の導入後に 7-A-13b で追記する**ので、**本書では書かない**。

### 3-4. トラブルシューティング

- 既存の「ログインできない」にある「DB を削除して再起動すると初回ユーザーが再作成されます」は、**ローカル（SQLite）限定**と明記する。**次を追記**（F15）：「`USERNAME`／`USER_PASSWORD` を変更しても、保存済みのハッシュは更新されません（`init_user()` は冪等）。**本番（Neon）での資格情報の変更手順は未整備です**（Render の無料プランでは Shell が使えません）。変更が必要なときは別途手順を整えます。」
- **追加する項目**：①`ModuleNotFoundError: No module named 'psycopg'`（`pip install -r requirements.txt` を実行）／`psycopg2`（`DATABASE_URL` のスキームが `postgresql://` のまま→`postgresql+psycopg://` に）②`pytest` が collection で失敗する（`DATABASE_URL` が接続URLのまま残っている→外して再実行）③ログインが 429（1分待つ。ログイン試行のレート制限）④（本番）初回アクセスが遅い（無料プランのスピンダウン・約1分）。

### 3-5. Render 本番運用手順（`## Render 本番運用手順` 以降）

**旧構成（Starter $7／Persistent Disk／SQLite）の記述は実態と異なる。** 次のとおり書き換える（F1・F2・F5・F11・F12）。

| 項目 | 変更 |
|---|---|
| 構成概要の表 | `nba-news-backend`：**Web Service（無料プラン）**・FastAPI バックエンドのみ（**バッチは動かさない**）。`nba-news-frontend`：Static Site（無料）。**追加**：Neon（PostgreSQL・無料）／GitHub Actions（バッチ）／healthchecks.io（外部 cron 監視）。**「Starter $7/月」「Persistent Disk（1GB $0.25/月）」は削除** |
| 手順 A（Blueprint 連携） | 維持。**`render.yaml` が正であり、ダッシュボードの値は sync で上書きされる**旨（F11）を追記 |
| 手順 B（シークレット） | 維持（5項目・`sync: false`）。**`DATABASE_URL` も `sync: false`（ダッシュボードで入力）**を追記 |
| 手順 C（URL プレースホルダーの更新） | **「現在は実 URL が `render.yaml` に設定済み。URL が変わる場合は `render.yaml` を編集して push する（ダッシュボードだけの変更は次の sync で上書きされる）。`render.yaml` に `YOUR_` 等のプレースホルダを残して push しない」**に書き換える。フロントの `VITE_API_BASE_URL` 変更後は再ビルドが必要（ビルド時環境変数）は維持 |
| **手順 D（Persistent Disk の確認）** | 🔴**削除**し、**「Neon の準備」に置き換える**：①Neon プロジェクトを作成（Free）②接続文字列は **Direct（Connection pooling をオフ）**を取得③スキームを **`postgresql://` → `postgresql+psycopg://`** に書き換える（`?sslmode=require` は残す。**入力欄の中で書き換え、チャット・Git・メモ帳に出さない**）④Render のダッシュボードで `DATABASE_URL` に設定⑤GitHub Secrets に登録（次項） |
| **新設：手順 E′（GitHub Actions バッチ）** | **GitHub Secrets（Settings → Secrets and variables → Actions）に `ANTHROPIC_API_KEY`・`BALLDONTLIE_API_KEY`・`DATABASE_URL`（Neon）を登録**（`HEALTHCHECK_PING_URL` は外部 cron 監視を使う場合のみ）。**`SECRET_KEY`・`USERNAME`・`USER_PASSWORD` は登録しない**（F5）。手動実行は Actions → NBA News Batch → Run workflow。定時実行の cron 式・遅延・欠落（F4）。**初回は Neon が空なので全記事が翻訳され Claude API の費用が発生する** |
| **新設：外部 cron 監視** | healthchecks.io の設定値（F7）。ping URL は秘密として扱う |
| 手順 E（デプロイ後の動作確認） | 維持。**「初回バッチ実行まで記事は0件の場合あり」は「GitHub Actions のバッチが一度実行されるまで」に**更新 |
| **新設：運用上の注意** | Auto-Deploy On・push のたびに再デプロイ（F11）／無料プランの制約（F12）／Neon 無料枠と目視確認（F13）。**週次チェックリストの整備は 7-B で行う**（本書では詳細を書かない） |

---

## 4. `README.md` の変更

| 箇所 | 変更内容 |
|---|---|
| 冒頭の説明 | 「個人用ローカルアプリです」→ **「個人利用の限定公開アプリです（ローカル実行も可能）」**（F1） |
| 主な機能 | 「RSS自動取得：…を4時間ごとに取得」に **「（本番は GitHub Actions の cron）」**を追記。「JWT認証」の項に**ログインのレート制限（5回/分・超過は 429）**を追記。データ自動削除は維持 |
| 技術スタック（表） | バックエンド：`Python 3.11 / FastAPI / SQLAlchemy / PostgreSQL（Neon）※ローカル既定は SQLite / slowapi / APScheduler（ローカル開発用）`。**行を追加**：バッチ＝GitHub Actions、ホスティング＝Render（無料）、監視＝healthchecks.io（F1・F6・F7） |
| ディレクトリ構成 | `CLAUDE.md` のツリーと**同じ内容**に揃える（`auth/`・`processor/dedup.py`・`api/limiter.py`・`run_batch_once.py`・`tests/`・ルートの `render.yaml`・`.github/workflows/batch.yml` の注記）。**README のツリーは現状 `auth/` と `dedup.py` が欠けている** |
| セットアップ §3（バックエンド依存パッケージ） | 🔴**手書きの `pip install fastapi uvicorn[standard] …` の一覧は削除し、`pip install -r backend/requirements.txt` のみにする**（一覧は `psycopg[binary]`・`slowapi` を含まず、**そのまま実行すると起動・テストが失敗する**） |
| 起動方法 | 「起動後、初回バッチが自動実行され…4時間ごとに自動更新」は**ローカル開発（`ENABLE_SCHEDULER` 既定 true）の動作**と明記し、**本番は GitHub Actions がバッチを実行する**ことを1文追記（F4・F6） |
| API エンドポイント（表） | **行を追加**：`PUT /api/settings`（設定の更新・要認証）・`GET /healthz`（認証不要）。`POST /api/auth/login` に「**5回/分を超えると 429**」を追記。`GET /api/schedule` に「`start_date`・`end_date` は `YYYY-MM-DD`（不正値は 422）」を追記。`GET /api/status` に「**`metrics`（運用指標）を含む**」を追記（F10）。**`POST /api/fetch` は存在しないので載せない** |
| 環境変数（表） | 必須5件は維持。**任意の変数**（`DATABASE_URL`・`ENABLE_SCHEDULER`・`ALLOWED_ORIGINS`・`HEALTHCHECK_PING_URL`）を `setup.md` の表と**同じ内容**で追加するか、`setup.md` への参照にする（**重複する場合は一方を正として参照にする**＝二箇所に同じ内容を書かない） |
| ログ | 「`logs/nba_news.log`」は**ローカル／Render の Web サービス**のログ。**バッチ（GitHub Actions）は標準出力のみで、Actions のジョブログで見る**ことを追記 |

---

## 5. 検証（Claude Code）

| # | 確認 | 期待 |
|---|---|---|
| 1 | **横展開 grep**：`grep -rn "SQLite\|APScheduler\|cron\|Persistent Disk\|Starter\|detail_design_p2\|basic_design_p2\|requirements_p2\|/api/fetch" CLAUDE.md setup.md README.md` | **残る箇所がすべて意図したもの**（ローカル開発の SQLite／APScheduler・GitHub Actions の cron・過去の記録としての p2 の言及など）。**意図しない残存があれば直す**。結果を一覧で報告 |
| 2 | **旧記述の消去確認**：`grep -n "cron方式は使用しない\|Starter \$7\|Persistent Disk（1GB" CLAUDE.md setup.md` | **0 件** |
| 3 | **シークレット混入なし**：文書内に API キー・接続文字列・パスワード（`sk-ant-` で始まる実値、`postgresql+psycopg://` の実在の資格情報等）が**書かれていない** | 例示は `xxxxx`・`ユーザー名` 等のみ |
| 4 | **コードとの突合**：`CLAUDE.md`・`setup.md` に書いた `config.py` の定数名・環境変数名・ファイル名が**実在する** | 実在しない名前が無い |
| 5 | **相互整合**：`CLAUDE.md`・`setup.md`・`README.md` の間で、ディレクトリ構成・環境変数・設計書の版が**食い違っていない** | 食い違い 0 件 |
| 5b | **`.env` ルールの存在確認**：`grep -n "\.env" CLAUDE.md` | 「Claude Code は `.env` を読まない」旨の記述が**1箇所以上**ある（値は表示しない） |
| 6 | `git diff --stat` | **`CLAUDE.md`・`setup.md`・`README.md` の3ファイルのみ**（コード・テスト・`.env.example` を含まない） |

---

## 6. 報告

1. 検証 #1〜#6 の結果（#1 は残存箇所の一覧と「意図したもの」の判定）。
2. **各ファイルの変更の要約**（節ごとに1〜2行）。
3. **確認できなかった事実・本書と実物が食い違った箇所**（例：環境変数の既定値、設計書の最新版）。
4. **`.env` 読み取り禁止ルールを `CLAUDE.md` に記載した箇所**（節名・行番号。決定済みのため確認不要。記載の事実のみ報告）。および、文書化すべきか迷った事項（あれば）。
5. commit は Takumi様が確認してから。

---

## 7. 7-A-13b（後半）に残すもの

| 項目 | 時期 | 理由 |
|---|---|---|
| フロントエンドのテスト実行手順（`npm test`・`npm run test:cov`）の `setup.md`・`README.md` への追記 | **7-A-8 の完了後** | テスト基盤が未導入（テスト設計書§9 #9） |
| 表記統一（`GLOSSARY`）・ラベル変更（F-14）に関する記述 | 7-A-6・7-A-7 の完了後 | 実装が未了 |
| 資格情報の変更手順（Shell 不要の手順）・週次チェックリスト | **7-B** | 未整備 |
| 横展開 grep の最終確認 | 7-A-13b | 7-A の最後 |
