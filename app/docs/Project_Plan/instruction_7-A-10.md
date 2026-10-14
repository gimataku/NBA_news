# 7-A-10 移行手順（Blueprint 版・v2）

- **対象**: フェーズ3 手順7 サブ手順 7-A-10（移行の実行 ＋ Health Check の継続可否の再判定）
- **版**: **v2（2026-10-14）**。v1（2026-10-13）を**実際に実行した手順**に合わせて書き直した
- **原典**: リスク調査書 v0.6 §1-4-9（11ステップ・ダッシュボード操作前提）。**Blueprint 連携（7-A-0 判定・状態A）では実行できないため組み替えた**
- **期限**: **2026-10-19**（開幕 2026-10-20 の前日）
- **主担当**: **Takumi様**（Render／Neon／GitHub Secrets ＝ シークレットの実値を扱う）
- **進捗**: 手順 1〜10 ✅（2026-10-14）／**ステップ11〜13・後片付けが未実施**（§5）。結果の詳細は `manufacturing_verification_log_p3.md` §7-A-10
- **姉妹文書**: `runbook_7-A-10_block1.md`（第1区の画面操作の詳細）／`instruction_7-A-10c_main_scheduler.md`（`main.py` の実装指示）

> **⚠️ シークレットの実値（Neon 接続文字列・APIキー・パスワード）をチャット・Git・メモ帳に出さない。** 共有するのは成否・件数・エラーの種類のみ。
> **⚠️ シェル**：手元 = PowerShell／Render Shell = bash（**無料プランでは Render Shell は使えない**）。

---

## 1. 原典からの主な組み替え

| 原典（ダッシュボード前提） | Blueprint 下での実際 |
|---|---|
| 5 ディスクのデタッチ／6 プラン変更／7 環境変数差し替え | **`render.yaml` の1回の編集（`disk:` 削除・`plan:` 変更・`ENABLE_SCHEDULER` 追加）に畳まれる**（7B）。ただし `DATABASE_URL` は**ダッシュボードで値を入れる**（`sync: false`）ので、**値の入力（7A）を構成変更（7B）より前に置く** |
| 8 手動デプロイ | **7C の push で自動デプロイが走る**（F7）ので不要になった |
| 9 動作確認 | **9A（接続先の確認）を新設**。ただし**無料プランでは Shell が使えず `engine.url` を出せない**ため、ログ・`last_fetched_at`・件数で代替 |
| 3 認証系はダミー値 | **登録しない**（7-A-1 の成果。バッチ経路は `auth` を import しない） |
| — | **第2区（5A・5C）を新設**：`DATABASE_URL` の所有権を、値を変えずに移して挙動を実測する |
| — | **7-A-10c を新設**：`main.py` の `ENABLE_SCHEDULER` 分岐を、**後戻り限界点の前に**入れておく |
| — | ステップ12・13：Health Check の再判定と `healthCheckPath` の去就 |

---

## 2. 前提と原則

### 2-1. 原則（F4・F7 の教訓）

| # | 原則 | 出典 |
|---|---|---|
| 1 | 🔴**Blueprint sync は、ダッシュボードの値を `render.yaml` の内容で上書きする。** 値だけでなく **`render.yaml` に書かれていない設定（Auto-Deploy 等）も既定値に戻りうる** | F4・F7 |
| 2 | **設定の「所有権」（どちらが正か）と「値」は別に動かす。** 同時に動かすと原因が切り分けられない | F4 教訓#5 |
| 3 | 🔴**「失敗しないこと」が最悪の失敗になりうる。** 空 DB・相対パス・環境変数の未反映は**エラーなしで起動する**。**件数（`total_articles`）と `last_fetched_at` の照合以外に気付く方法がない** | F4 |
| 4 | 🔴**「保護の設定」（Auto-Deploy Off 等）は、保護される操作の直前に実測で確かめる。** 設定した時点の確認は、その後の sync で無効になりうる | F7 |
| 5 | `render.yaml` の編集は**まとめて・最小回数**。この移行では **5A（1回目）と 7B（2回目）** | F4 |
| 6 | 後戻り限界点は **7C**（`disk:` 削除の同期＝SQLite データの破棄）。それより前は、構成を戻せば原状に戻る | — |

### 2-2. 前提作業（すべて ✅・2026-10-13）

| 前提 | 内容 | 結果 |
|---|---|---|
| **A** | `render.yaml` に `YOUR_` が **0件**・全 `value:` が実値・シークレット5件が `sync: false` | ✅ `ALLOWED_ORIGINS=https://nba-news-frontend.onrender.com`／`VITE_API_BASE_URL=https://nba-news-backend-ppsd.onrender.com` |
| **B** | `db/migrate_p2.py` に `://` を含む `DATABASE_URL` を拒否するガード（3行） | ✅ 4ケース確認・`pytest` 90 passed |
| **C** | ロールバック手段（§6） | ✅ 確認済み |
| **D** | Render の挙動3件 | ✅ **5A で実測**（下記） |

**前提D の実測結果（2026-10-14・5A）**

| # | 問い | 結果 |
|---|---|---|
| ① | `DATABASE_URL` を `sync: false` にすると、ダッシュボードの値はどうなるか | ✅**値は残る**（5B は不要だった） |
| ② | sync とデプロイを分離できるか | ✅**できる**（バックエンドはデプロイされず、フロントのみ走った） |
| ③ | Auto-Deploy Off でも sync は走るか | ✅**走る** |

> 🔴**ただし 5A の sync により Auto-Deploy の設定が On に戻った可能性が高い**（F7）。ステップ2 の push（5A より前）はデプロイが走らず、7-A-10c の push（5A より後）は走った。**以降の手順は「Auto-Deploy が On でも壊れない順序」で書いてある。**

### 2-3. Neon の接続文字列（ステップ1・7A で使う）

| 項目 | 内容 |
|---|---|
| エンドポイント | 🔴**Direct（非プール）**。Connect 画面で **Connection pooling のチェックを外す**。pooler は PgBouncer（transaction モード）で psycopg 3 のプリペアドステートメントと相性が悪い |
| スキーム | 🔴Neon は `postgresql://` を提示する。**`postgresql+psycopg://` に書き換える**（そのままだと `psycopg2` を探して `ModuleNotFoundError`） |
| 末尾 | `?sslmode=require` は残す。**`+psycopg` 以外は1文字も変えない** |
| 取り扱い | **入力欄の中で書き換える**（GitHub Secrets・Render とも）。チャット・Git・メモ帳に出さない |
| 無料枠 | 1 GB／プロジェクト・**100 CU-hours／月**・**5 GB 転送／月**・5分で scale-to-zero。**CU-hours・転送の超過は次の請求期間までコンピュート停止**（超過課金なし）。**観測手段がない**ため週次チェックリスト（7-B）に載せる |

### 2-4. 🔴 コメントアウトして後で戻す箇所（2つ）

| # | 箇所 | 戻すタイミング | 忘れた場合 | 気付けるか |
|---|---|---|---|---|
| 1 | **`batch.yml` の `schedule:`** | **ステップ10** | 🔴**記事取得が完全に停止する** | ❌**静か**。`last_fetched_at` が止まるのを目視で拾うまで最大1週間 |
| 2 | **`models.py` の旧コードブロック**（コメントアウト部） | **後片付け（§5-5）** | 実害なし（コメント）。残ると誤読を招く | — |

> **#1 のほうが危険である。** チェックリストで独立した1行にする（計画書§8-0-1）。

---

## 3. 手順（実行した順・結果つき）

### 🟢 第1区：準備（本番に影響しない）── ✅

| # | 作業 | 実績・注意 |
|---|---|---|
| 0 | Render バックエンドの **Auto-Deploy を Off** | ⚠️**5A の sync で On に戻りうる**（F7） |
| 1 | Neon プロジェクト作成・**Direct 接続文字列**取得・`postgresql+psycopg://` に書き換え | 詳細は runbook §1。**アカウント未作成なら 1-0 から** |
| 2 | `db/models.py` のコメント切替（新コード有効化）＋ `migrate_p2.py` のガードを1コミットで push | Auto-Deploy Off のため**デプロイは走らなかった**（この時点では） |
| **2.5** | ローカル接続確認：`pip install -r requirements.txt` → `$env:DATABASE_URL` 設定 → `driver: psycopg`・`select 1 = 1` → **`Remove-Item Env:\DATABASE_URL`** | 🔴**ステップ2 の後**。**前に実行すると `driver: pysqlite`**（旧コードが `sqlite:///postgresql+psycopg://…` を組み立てる）。**psycopg が未導入だと pytest の collection が壊れる**（実測） |
| 3 | GitHub Secrets **3件**：`ANTHROPIC_API_KEY`・`BALLDONTLIE_API_KEY`・`DATABASE_URL`（Neon） | 🔴**認証系3件は登録しない**。`HEALTHCHECK_PING_URL` は 7-A-12 まで未登録 |
| 4 | Actions → NBA News Batch → **Run workflow** で初回バッチ | ✅**緑／`INFO` ログあり／`articles`>0／`users`=0** の3条件。**Claude API の費用が発生**するため成功するまで回さない |
| 4.5 | `pytest`（**`DATABASE_URL` を外した状態**） | **90 passed** |

> 🔴**ステップ4 が成功しないまま先へ進んではならない。** 以降で SQLite を捨てるため、**Neon にデータが入る経路が機能していることを、捨てる前に実証する**のが本区の目的。

### 🟡 第2区：`DATABASE_URL` の所有権を移す（値は変えない）── ✅

| # | 作業 | 実績 |
|---|---|---|
| **5A** | `render.yaml`：`DATABASE_URL` を `sync: false` に変更＋「例:」コメント4行（L31-32・L43-44）削除 → push | **`plan`・`disk`・`ALLOWED_ORIGINS`・`VITE_API_BASE_URL` は触らない**。前提D の3件が実測できた |
| 5B | 値が空なら `/data/nba_news.db` を入力 | **不要**（値は残った） |
| 5C | フロントのデプロイ成功・ニュース一覧表示・`/api/status` の `total_articles` を確認 | ✅ **360**。🔴**合格条件は「358一致」ではなく「同一 DB で単調に増える（0 でも基準値未満でもない）」**（旧スケジューラが稼働中のため増える） |

> 🔴**本区のあと、`DATABASE_URL` がスキームなしの間は、バックエンドを手動デプロイしてはならない。** 新コードは起動に失敗する。**Auto-Deploy が On に戻っている可能性があるため、push も同じ結果になる**（F7）。

### 🟡 7-A-10c：`main.py` の `ENABLE_SCHEDULER` 分岐 ── ✅

| 項目 | 内容 |
|---|---|
| 指示文 | `instruction_7-A-10c_main_scheduler.md`（基本設計書 v0.8 §5-3・テスト設計書 T-P3-16） |
| 変更 | `scheduler.start()`・`check_and_run_batch()`・`scheduler.shutdown()` の3箇所を `_scheduler_enabled()`（既定 true）で分岐。`init_db()`・`init_user()` は対象外 |
| 結果 | `pytest` **99 passed**（90＋9）。**`ENABLE_SCHEDULER` を 7B で `false` にしても、コードが先に載っている状態にした** |
| ⚠️ F7 | **この push でバックエンドの自動デプロイが走り、失敗した**（`DATABASE_URL` がスキームなし）。**Live は旧版のまま・データ無傷**。以降は「自動デプロイが走る前提」で進める |

### 🔴 第3区：後戻り限界点の前の記録 ── ✅

| 作業 | 値（2026-10-14） |
|---|---|
| 6-準備：`/api/status` の指標を記録 | `total_articles`=**360**／`articles_last_7d`=**92**／`by_category_7d` column 41・injury 17・trade_fa 34／`duplicate_count` 8／`last_fetched_at`=`2026-10-13T13:47:21` |

**チェックリスト（すべて ✅ を確認してから第4区へ）**：前提A・B・C・D／ステップ4（Neon に記事）／5C／7-A-10c／6-準備。

### 🔴 第4区：切り替え ── ✅

| # | 作業 | 実績・注意 |
|---|---|---|
| **7A** | Render バックエンド → Environment → Edit。🔴**1回の保存で2つ**：`DATABASE_URL`＝Neon の接続文字列（入力欄の中で `postgresql+psycopg://` に書き換え・`?sslmode=require` を残す）／`ENABLE_SCHEDULER`＝`false`（新規）。保存は **Save only** | 🔴**片方だけ先だと、新コード＋Neon＋旧スケジューラで GitHub Actions と二重実行になる**。「Save only」が無ければ「Save, rebuild, and deploy」で可（両方揃うため）。**この時点では SQLite はディスクに残っており、`DATABASE_URL` と `ENABLE_SCHEDULER` を戻せば旧コードへ Rollback できる** |
| **7B** | `render.yaml` を**1回の編集で**変更：①`plan: starter` → **`plan: free`**／②`disk:` セクション（4行）**削除**／③`ENABLE_SCHEDULER` を通常値に追加（`value: "false"`・**引用符つき**） | `git diff render.yaml` で上の3か所だけが差分であることを確認。**`healthCheckPath`・シークレット5件・`DATABASE_URL`・`HOST`・`ALLOWED_ORIGINS`・フロント側は触らない** |
| **7C** | `git add render.yaml` → commit → push | 🔴**ここで `disk:` 削除が同期され、SQLite（旧データ）は失われる**＝**後戻り限界点**。Neon には初回バッチ分が入っている。**ユーザーは Neon の `users` が空なので、`USERNAME`／`USER_PASSWORD` の環境変数から `init_user()` が再作成する** |
| 8 | 手動デプロイ | **不要**（7C で自動デプロイが走り、成功した）。走らなければ Manual Deploy |

### 🟢 第5区：確認 ── ✅（9A〜9C）

| # | 作業 | 合格条件・実績 |
|---|---|---|
| **9A** | 接続先の確認（**Shell 不可の代替**）：①Render ログに **`Scheduler disabled (ENABLE_SCHEDULER=false)`** があり **`Scheduler started` がない**／②`/api/status` の **`last_fetched_at` が移行前の値（`2026-10-13T13:47:21`）でない**／③`total_articles` が **移行前の値（360）でも 0 でもない** | ✅ログ OK／`last_fetched_at`=`2026-10-13T15:17:41`（ステップ4 のバッチ時刻）／`total_articles`=**15**。🔴**`0` は環境変数が効かず空のローカル DB に落ちた状態**（正常起動するため必ず確認） |
| **9B** | `/api/status` の `total_articles` が Neon に入れた件数と整合 | ✅ 15（SQLite の 360 は捨てたので一致しないのが正しい） |
| **9C** | ログイン（`USERNAME`／`USER_PASSWORD`）・一覧に記事が表示・`/healthz` が 200 | ✅（無料プランのスピンダウン復帰に約1分かかる） |

---

## 4. 実行中に判明した事象（要点）

| # | 事象 | 対処 |
|---|---|---|
| F7 | Auto-Deploy が On に戻っていた（5A の sync による上書きの疑い）。7-A-10c の push で自動デプロイが走り失敗 | **「On でも壊れない順序」に組み替え**（7A で2変数を同時設定）。Live は旧版のまま残り被害なし |
| — | `driver: pysqlite` | ステップ2.5 を2の**後**に置く（旧 runbook の 1.5 は順序誤り） |
| — | `pytest` collection 7件のエラー（`No module named 'psycopg'`） | `pip install -r requirements.txt`＋`Remove-Item Env:\DATABASE_URL`。**テスト設計書 v0.7 で `conftest.py` に `DATABASE_URL` のダミー値を追加**（§6-4「無改修で済む」は条件付きだった） |
| — | `total_articles` が 358→360 | 旧スケジューラの取得分。合格条件を「単調増加」に読み替え |
| — | 無料プランで Render Shell が使えない | 9A を代替。**資格情報の変更手順を Shell 前提にしない**（7-B・setup.md へ引き継ぎ） |

---

## 5. 残りの手順（Takumi様・2026-10-15 以降）

### 🔴 ステップ10：`batch.yml` の `schedule:` を有効にする ── ✅（2026-10-14）

対象：`NBA_news\.github\workflows\batch.yml`（`app/` の外）。`schedule:` と `cron` 行の先頭の `#` を外す（インデント維持・`workflow_dispatch:` は残す）。

```yaml
on:
  schedule:
    - cron: "0 21,1,5,9,13,17 * * *"   # JST 6/10/14/18/22/2 時
  workflow_dispatch:
```

```powershell
Select-String -Path .github\workflows\batch.yml -Pattern "schedule|cron|#"
git add .github/workflows/batch.yml
git commit -m "ci: batch.yml の schedule を有効化（Neon移行完了）"
git push
```

| 確認 | 期待 |
|---|---|
| `Select-String` | `schedule:`・`cron` の行が `#` で始まらない |
| 最初の定時（JST 6・10・14・18・22・2 時。GitHub は数分〜15分遅れうる）で Actions に **schedule 契機の NBA News Batch** が実行される | ✅緑 |
| 実行後の `/api/status` の `last_fetched_at` | 更新されている |

> ✅**2026-10-14 実施・定時実行2回成功。** 🟡**ただし GitHub の定時実行は遅延（約45分）・欠落（10:00 の枠）しうる**（7-A-12 で外部cron監視の猶予を決める際の実測値）。
>
> 🔴**これを忘れると記事取得が止まり、静かに進行する。** Render 側スケジューラは `ENABLE_SCHEDULER=false` で停止済みなので、取得を担うのは GitHub Actions だけである。

### ステップ11：Auto-Deploy の確認と復帰

| 作業 | 内容 |
|---|---|
| 現在値の確認 | Render バックエンド → Settings → Build & Deploy → **Auto-Deploy**。F7 の仮説（On に戻っている）を確かめる |
| 判断 | **通常運用は Auto-Deploy On でよい**（F7 以降に Off を維持する理由はない）。**On のまま運用するなら、以後の push はすべてデプロイを誘発する**ことを前提にする |
| 🟡 明示の要否 | **`render.yaml` に `autoDeploy: true` を書いて sync での上書きを防ぐ**かを、ステップ13 の編集（`healthCheckPath` の要否）と**同じ編集にまとめて**判断する（編集回数を増やさない） |

### ステップ12：Health Check 通知の継続可否の再判定

| 確認 | 方法 |
|---|---|
| ① 無料プランで通知が使えるか | Render → Settings → Notifications／Health Check の項目が有効か |
| ② **スピンダウン（15分の無アクセス）を障害と誤判定して鳴り続けないか** | 15分以上放置した後の Events・メールを確認 |
| ③ 継続／停止の決定 | **鳴りっぱなしなら止める**（リスク評価書§4-1-4 ②）。**7-A-2 は F2（通知が届かない）で ❌未達のまま**であり、**ここで「再挑戦／廃止」を決める** |

### ステップ13：`healthCheckPath` を `render.yaml` に残すか

ステップ12 の結論に従う。**継続なら残し、廃止なら削除**（`render.yaml` の編集はステップ11 の `autoDeploy` 判断とまとめて1回にする）。

### 5-5. 後片付け：`models.py` の旧コードブロックの削除

- 削除するのは `# 旧コード（7-A-10 完了後に削除する）` 以下のコメントアウト3行（`DB_PATH`・`engine` の旧定義）。新コード2行と `SessionLocal` 以降は変更しない。
- `pytest`（`DATABASE_URL` を外した状態）が全件 passed であることを確認し、push する（Auto-Deploy On なら再デプロイが走る。**設定が揃っているので問題ない**）。
- 実施は Claude Code（指示文は別途）。

---

## 6. 撤退・ロールバック

| 時点 | 戻し方 | データ |
|---|---|---|
| **第1〜2区（〜5C）** | `git revert`（models.py）。Neon プロジェクトは削除してよい。`render.yaml` の `sync: false` は `value: /data/nba_news.db` に戻して push | **無傷** |
| **第3〜4区の 7A まで** | `DATABASE_URL`・`ENABLE_SCHEDULER` を元に戻し、旧コードを Rollback。**SQLite はディスクに残っている** | 無傷 |
| **7C 以降（後戻り限界点）** | **データは戻らない**。戻せるのは構成のみ：`plan` を starter に・ディスクを再作成・`DATABASE_URL` を **`sqlite:////data/nba_news.db`（スラッシュ4本）** に・**旧コードごと**デプロイ（**新コードの `models.py` は `check_same_thread=False` を持たないため SQLite では動かさない**）。記事は再取得で埋まるが30日分が揃うまで時間がかかる | 失われる |
| 不合格時の判断基準 | **ログイン不可・記事が表示されない等の機能不全は撤退**。**起動待ちの長さ・UX の劣化は撤退理由にしない**（§1-4-1 で許容済み） | — |

---

## 7. 完了判定

| # | 項目 | 状態 |
|---|---|---|
| 1 | 前提 A・B・C・D | ✅ |
| 2 | 第1区（0〜4.5） | ✅ |
| 3 | 第2区（5A・5C） | ✅ |
| 4 | 7-A-10c | ✅ |
| 5 | 6-準備（360／92 ほか） | ✅ |
| 6 | 7A・7B・7C（切替・デプロイ成功） | ✅ |
| 7 | 9A・9B・9C | ✅ |
| 8 | **ステップ10**（`schedule:` 解除・最初の定時実行が緑・`last_fetched_at` 更新） | ✅（定時 #2 JST 06:43・#3 JST 14:49 が成功。10:00 の枠は欠落＝GitHub の仕様・7-A-12 の設計値へ引き継ぎ） |
| 9 | ステップ11（Auto-Deploy の確認） | ⬜ |
| 10 | ステップ12・13（Health Check の再判定・`healthCheckPath` の去就） | ⬜ |
| 11 | 後片付け（`models.py` 旧コード削除） | ⬜ |

> **7-A-10 は 8〜11 が済むまで ✅ にしない**（計画書§4「✅判定ルール」）。8 の取り忘れは静かに進行する失敗のため、**翌日の最初の報告で必ず確認する**。
