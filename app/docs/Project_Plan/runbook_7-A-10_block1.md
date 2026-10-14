# 7-A-10 第1区 作業手順書（準備・本番無傷）

- **対象**: `instruction_7-A-10.md` §3 第1区（ステップ0〜4.5）
- **作成日**: 2026-10-13（**v2：2026-10-14 改訂**・実行結果を反映。ステップ1.5 → **2.5** に採番し直し）
- **主担当**: **Takumi様**
- **性質**: 🟢**この区間は何度でもやり直せる。** 本番は無傷で、`git revert` ＋ Auto-Deploy On ＋ Neon プロジェクト削除で原状復帰する（**第1区は ✅完了・2026-10-14**。後続の区は `instruction_7-A-10.md` v2）
- **前提**: 前提A ✅／前提B ✅／前提C ✅（`instruction_7-A-10.md` §2）

> **⚠️ シークレットの実値をチャットに出さない。** Neon の接続文字列・APIキー・パスワードはいずれも対象。共有するのは**成否・件数・エラーの種類**のみ。
>
> **⚠️ シェルの区別**：**手元 = PowerShell**／**Render Shell = bash**。本書は手元の作業は PowerShell で書く。

---

## ステップ0：Render の Auto-Deploy を Off にする

### 操作

1. Render ダッシュボード → **`nba-news-backend`** を開く
2. 左メニュー **Settings**
3. **Build & Deploy** セクション内の **Auto-Deploy** を探す
4. **`No`**（または Off）に変更し、**Save** する

### 確認

- 画面を再読込し、**Auto-Deploy が `No` のまま**であること

### なぜ最初か

🔴 **F4（2日間のログイン不能）は Auto-Deploy On のまま `models.py` を push したために起きた。** ステップ2 で同じ push をするため、**先に止める**。

> **⚠️ フロントエンド（`nba-news-frontend`）の Auto-Deploy は触らない。** 本区間でフロントのコードは変更しないため、影響しない。

---

## ステップ1：Neon プロジェクトの作成と接続文字列の取得

### 1-0 🆕：アカウント作成（未サインインの場合）

**Takumi様ご自身で行う。** 当方はアカウント作成・パスワード入力を行わない。

1. **https://neon.com** を開き **Sign up**
2. サインイン方法を選ぶ（GitHub／Google／メールアドレス）。**技術的な差はない**ため任意
3. **Free プランを選ぶ。クレジットカードの登録は不要**
4. サインアップ直後に**プロジェクト作成の画面**が出る → 1-1 へ

#### 🔴 無料枠の最新条件（2026-10-13 に公式ドキュメントで確認）

| 項目 | 現在の上限 | 本プロジェクトの記録 | 差 |
|---|---|---|---|
| **ストレージ** | **1 GB／プロジェクト**（アカウント全体で 20 GB） | 0.5 GB | ✅**2倍に緩和**（2026-10-02 の変更） |
| **コンピュート** | **100 CU-hours／プロジェクト／月** | 100 CU-hours | ✅一致 |
| **ネットワーク転送** | **5 GB／プロジェクト／月** | 🔴**記録に無い** | ⚠️**新たに把握した制約**（下記） |
| プロジェクト数／ブランチ数 | 100／10 | — | — |
| **Scale to zero** | **5分の無操作でコンピュート休止**（無料プランでは無効化できない） | 「無操作で休止する」と記載 | ✅**具体値を把握**（5分） |

> **✅ 7-A-0 ②（無料枠の条件の再確認・2026-09-12「問題ない」）以降、条件は*緩和*されている。** ストレージが倍になり、他は同等。**移行の前提は崩れていない。**
>
> **上限に達したときの挙動**
>
> | 超過するもの | 起こること |
> |---|---|
> | **CU-hours／ネットワーク転送** | 🔴**次の請求期間までコンピュートが停止する**。既存接続は切れ、新規接続もできない |
> | **ストレージ（1 GB）** | **INSERT／UPDATE／DELETE が失敗する**（容量を空けるかアップグレードするまで） |
> | いずれも | **無料プランでは超過課金されない** |
>
> **本プロジェクトでの見通し**
>
> | 項目 | 試算 | 判定 |
> |---|---|---|
> | ストレージ | 記事358件 × 要約800〜1200字 ＋ 試合日程 ＝ **数MB規模** | ✅**1 GB に対して桁違いに余裕** |
> | CU-hours | バッチ 6回/日 × 数分 ＋ 閲覧時の起動（5分単位）→ **月10 CU-hours 前後の見込み** | ✅**100 に対して余裕** |
> | **ネットワーク転送** | 個人利用1名・記事は要約テキストのみ | ✅**5 GB に対して余裕** |
>
> 🔴**ただし CU-hours・ネットワーク転送のいずれも観測手段がない。** `/api/status` の `metrics` にも含まれず、要件定義書§4-1 の指標にも無い。**リスク評価書が「Neon CU-hours に観測機構が無い」として週次チェックリスト項目にしたのと同じ扱いが、ネットワーク転送にも必要**である。
>
> **引き継ぎ**: **週次チェックリスト（7-B で改訂）に「Neon ダッシュボードで CU-hours と *ネットワーク転送* の消費を目視する」を1項目として立てる。** 超過すると**次の請求期間まで復旧しない**（最大1か月）ため、**事後の検知では間に合わない**。

### 1-1. プロジェクト作成

1. Neon にサインイン → **New Project**
2. 設定

| 項目 | 推奨 | 理由 |
|---|---|---|
| **Region** | **Render のサービスと同じ／近いリージョン**（Render 既定は US West・Oregon なので **AWS us-west-2**） | レイテンシ。API が1リクエストごとに数クエリ投げるため効く |
| Postgres version | **既定のまま** | 設計は特定バージョンに依存しない |
| Database name | **既定のまま**（`neondb` 等） | `DATABASE_URL` に含まれるため、名前自体は何でもよい |
| **Compute size** | **最小（0.25 CU 等の既定）** | 🔴**無料枠は月 100 CU-hours**。大きくすると枠を早く使い切る |

### 1-2. 接続文字列の取得 ── 🔴 **Direct（非プール）を選ぶ**

Neon の接続文字列には2種類ある。

| 種類 | ホスト名 | 採否 |
|---|---|---|
| **Direct（非プール）** | `ep-xxxx.us-west-2.aws.neon.tech` | ✅**こちらを使う** |
| Pooled（プール） | `ep-xxxx-**pooler**.us-west-2.aws.neon.tech` | ❌**使わない**（下記） |

> **Pooled を避ける根拠**: Neon の pooled エンドポイントは **PgBouncer の transaction モード**である。一方 **psycopg 3 は既定でサーバサイドのプリペアドステートメントを使う**（同一クエリが5回を超えると有効化）。**この2つは相性が悪く、断続的なエラーを起こしうる**。
>
> 回避するには `prepare_threshold=None` 相当の設定が必要だが、**`models.py` の `create_engine()` に接続オプションを足す変更になる**——設計書§3-4 に無い変更であり、**本移行で増やしたくない**。
>
> **Direct なら PgBouncer を通らないため、この問題は起きない。** SQLAlchemy は自前のコネクションプールを持っており、`pool_pre_ping=True`（§3-4）で休止後の切れた接続も掴み直せる。**プール機能は SQLAlchemy 側で足りている。**

### 1-3. 🔴 スキームの書き換え

**Neon が提示する文字列は `postgresql://` で始まる。これを書き換える。**

```
変更前： postgresql://ユーザー:パスワード@ep-xxxx.us-west-2.aws.neon.tech/neondb?sslmode=require
変更後： postgresql+psycopg://ユーザー:パスワード@ep-xxxx.us-west-2.aws.neon.tech/neondb?sslmode=require
         ^^^^^^^^^^^^^^^^^^^
```

| 形式 | SQLAlchemy が探すドライバ | 結果 |
|---|---|---|
| `postgresql://` | **`psycopg2`** | 🔴 `ModuleNotFoundError: No module named 'psycopg2'` |
| **`postgresql+psycopg://`** | **`psycopg`（3系）** | ✅ 正しい |

> **`+psycopg` 以外は1文字も変えない。** ユーザー名・パスワード・ホスト・DB名・`?sslmode=require` はそのまま。
>
> **書き換えた文字列を安全な場所に控えておく。** ステップ3（GitHub Secrets）とステップ7A（Render 環境変数）の**2箇所で使う**。

---

## ステップ2：`models.py` の切り替えと push

### 2-1. `models.py` L81-86 のコメントを入れ替える

**変更前（現在・F4 復旧の状態）**

```python
# --- DB初期化 ---
# 新コード
# DB_PATH = os.getenv("DATABASE_URL", "sqlite:///nba_news.db")
# engine  = create_engine(DB_PATH, pool_pre_ping=True)
# 旧コード
DB_PATH = os.getenv("DATABASE_URL", "nba_news.db")
engine  = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
```

**変更後**

```python
# --- DB初期化 ---
# 新コード（フェーズ3・DATABASE_URL は接続URL全体。詳細設計書§3-4）
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///nba_news.db")
engine  = create_engine(DB_PATH, pool_pre_ping=True)
# 旧コード（7-A-10 完了後に削除する）
# DB_PATH = os.getenv("DATABASE_URL", "nba_news.db")
# engine  = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
```

**L87 `SessionLocal = sessionmaker(...)` 以降は変更しない。**

### 2-2. ローカル確認（push 前）

```powershell
cd C:\Users\gimatakumi\Documents\projects\NBA_news\app\backend
python -c "from db.models import engine; print(engine.url)"
```

**期待**: `sqlite:///nba_news.db`（`DATABASE_URL` 未設定なので既定値が効く）

```powershell
pytest
```

**期待**: **90 passed**（`conftest.py` が自前のエンジンを使うため通る。🔴**ただし `DATABASE_URL` を外した状態で**。接続URL形式が残っていて psycopg が未導入だと collection でエラーになる）

### 2-3. コミットと push

```powershell
cd C:\Users\gimatakumi\Documents\projects\NBA_news
git status
git add app/backend/db/models.py app/backend/db/migrate_p2.py
git commit -m "7-A-10: DATABASE_URL を接続URL形式に切り替え、migrate_p2 にガードを追加"
git push
```

> **`migrate_p2.py` のガードが既にコミット済みなら `git add` から外す。** `git status` で確認する。

### 2-4. 🔴 Deploys タブの確認（**本区間で最も重要な確認**）

1. Render → `nba-news-backend` → **Deploys** タブ
2. **新しいデプロイが開始されていないこと**を確認

| 結果 | 意味 | 対処 |
|---|---|---|
| **新しいエントリが無い** | ✅**Auto-Deploy Off が効いている**（前提D③ の実測） | 次へ進む |
| 🔴**新しいデプロイが走り始めた** | **Auto-Deploy が止まっていない** | 🔴**即座に Cancel**。放置すると `create_engine("/data/nba_news.db")` で**起動失敗**し、F4 の再現になる |

> 🔴**この確認は「ステップ2 の時点では Off が効いていた」ことしか保証しない。** 後続の `render.yaml` の push（第2区 5A）の sync で **Auto-Deploy が On に戻りうる**（F7・2026-10-14）。**以降の push の直前にも、同じ確認が要る。**
>
> **Cancel が間に合わなかった場合**: デプロイは失敗するが、**Render は直前の正常なデプロイを live のまま維持する**ため、本番は動き続ける。慌てずに Auto-Deploy の設定を直し、**Deploys タブで live のコミットが変わっていないこと**を確認する。

---

## ステップ2.5：ローカルで接続を確認する（**コスト0**・ステップ2の*後*）

**ステップ4（初回バッチ）は Claude API を使うため有料である。その前に、接続とドライバだけを無料で確かめる。**

### 操作（手元・PowerShell）

```powershell
cd C:\Users\gimatakumi\Documents\projects\NBA_news\app\backend
pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://...書き換え済みの文字列..."
python -c "from db.models import engine; from sqlalchemy import text; print('driver:', engine.url.get_driver_name()); c = engine.connect(); print('select 1 =', c.execute(text('select 1')).scalar()); c.close()"
```

### 期待される出力

```
driver: psycopg
select 1 = 1
```

### 失敗したときの読み方

| 出力 | 原因 | 対処 |
|---|---|---|
| `ModuleNotFoundError: No module named 'psycopg2'` | **スキームが `postgresql://` のまま** | 1-3 の書き換えをやり直す |
| `ModuleNotFoundError: No module named 'psycopg'` | **`psycopg[binary]` が未インストール** | `pip install -r requirements.txt` を実行（7-A-9a で追記済み） |
| `could not translate host name` | ホスト名の誤り | 文字列をコピーし直す |
| `password authentication failed` | 認証情報の誤り | 同上 |
| `SSL connection has been closed` 等 | `?sslmode=require` が落ちている | 末尾を確認 |
| `ArgumentError: Could not parse SQLAlchemy URL` | 文字列の破損（改行混入など） | 1行であることを確認 |

> 🔴 **順序は 0 → 1 → 2 → 2.5 → 3 → 4 → 4.5。** ステップ2（`models.py` の新コード有効化）の**前**に実行すると、**旧コードが `sqlite:///postgresql+psycopg://...` を組み立てて `driver: pysqlite` になる**（実測・2026-10-14）。
>
> 🔴 **`pip install -r requirements.txt` が先に必要**。`psycopg[binary]`（7-A-9a で追記済み）が未導入だと `ModuleNotFoundError: No module named 'psycopg'` になり、**同じセッションで `pytest` を走らせると collection の段階で 7 件がエラー**になる（`db/models.py` のモジュールレベル `create_engine()` が import 時に走るため。実測）。

### 終わったら環境変数を消す

```powershell
Remove-Item Env:\DATABASE_URL
python -c "import os; print('DATABASE_URL' in os.environ)"
```

**期待：`False`**。🔴 **消し忘れると、同じ PowerShell セッションでの `pytest` や `python main.py` が Neon を見てしまう**（実測：別ウィンドウで消して残っていた）。

---

## ステップ3：GitHub Secrets の登録（4件）

### 操作

1. GitHub → リポジトリ → **Settings**
2. 左メニュー **Secrets and variables** → **Actions**
3. **New repository secret** で1件ずつ追加

| Name | Secret | 備考 |
|---|---|---|
| `ANTHROPIC_API_KEY` | 既存のキー | — |
| `BALLDONTLIE_API_KEY` | 既存のキー | — |
| `DATABASE_URL` | **1-3 で書き換えた文字列** | 🔴`postgresql+psycopg://` で始まること |
| `HEALTHCHECK_PING_URL` | **登録しない（または空）** | 7-A-12 で決まる。未設定なら `run_batch_once.py` がスキップする（§2-1 制約9） |

### 🔴 登録しないもの

| Secret | 理由 |
|---|---|
| `SECRET_KEY` | **7-A-1 の成果。** バッチ経路は `auth` を import しない（推移的 import 9ファイルで確認済み） |
| `USERNAME` | 同上 |
| `USER_PASSWORD` | 同上 |

> **原典（リスク調査書§1-4-9 ステップ3）は「認証系はダミー値」としていたが、7-A-1 の完了により*登録そのものが不要*になった。** ダミー値も入れない。

### 確認

- Secrets の一覧に **3件**（`ANTHROPIC_API_KEY`・`BALLDONTLIE_API_KEY`・`DATABASE_URL`）が並ぶこと
- 🔴**認証系3件が無いこと**

---

## ステップ4：`workflow_dispatch` で初回バッチを実行

### 操作

1. GitHub → **Actions** タブ
2. 左の一覧から **NBA News Batch**
3. 右上の **Run workflow** → ブランチは既定（`main`）→ **Run workflow**

> 🔴**`batch.yml` の `schedule:` のコメントは解除しない。** 解除はステップ10 である。

### 4-1. ジョブの結果

| 確認 | 期待 |
|---|---|
| ジョブのステータス | ✅**成功（緑のチェック）** |
| 所要時間 | 数分（記事件数に依存） |

### 4-2. 🔴 ログに `INFO` の進行ログが出ているか

ジョブ → **Run batch** ステップを展開し、以下のような行があることを確認する。

```
2026-10-13 ... INFO scheduler: ...
```

| 結果 | 意味 |
|---|---|
| `INFO` 行がある | ✅**7-A-9 で `logging.basicConfig()` を足した効果が出ている** |
| 🔴`INFO` 行が無く、エラーだけ | `basicConfig` が効いていない。`run_batch_once.py` L16-20 を確認 |

### 4-3. 🔴 Neon に記事が入ったか

Neon ダッシュボード → **SQL Editor** で実行。

```sql
SELECT count(*) FROM articles;
```

| 結果 | 判定 |
|---|---|
| **0 より大きい** | ✅**合格**。Neon にデータが入る経路が機能している |
| **0** | 🔴**不合格**。先へ進んではならない |
| `relation "articles" does not exist` | 🔴 `init_db()` が走っていない。ジョブのログを確認 |

あわせて確認。

```sql
SELECT count(*) FROM users;
```

**期待：0**。🔴**`init_user()` を呼んでいない**ことの確認である（§2-1 制約2・7-A-1 の目的）。**1 以上なら、バッチが認証系に触れている**ことになり設計違反。

### 4-4. よくある失敗と読み方

| ログのエラー | 原因 | 対処 |
|---|---|---|
| `ModuleNotFoundError: No module named 'psycopg2'` | スキームが `postgresql://` のまま | Secret `DATABASE_URL` を書き直す |
| `RuntimeError: ANTHROPIC_API_KEY / BALLDONTLIE_API_KEY が未設定です` | APIキーの Secret 名が違う／未登録 | Secret 名を `batch.yml` の `env:` と突き合わせる |
| `RuntimeError: SECRET_KEY が未設定です` | 🔴**`auth` が import されている** | **設計違反**。`run_batch_once.py` に `init_user` が混入していないか確認（7-A-9 レビュー観点2） |
| `ArgumentError: Could not parse SQLAlchemy URL` | 文字列の破損・改行混入 | Secret を1行で貼り直す |
| `batch failed: ...` ＋ 終了コード1 | RSS 全ソース失敗（§3-1-1 失敗#1） | **設計どおりの挙動**。時間を置いて再実行 |

### ⚠️ 本ステップはコストが発生する

**Neon は空なので全記事が新規に見え、RSS 全件が Claude API で翻訳される。** 意図どおりだが、**1回分の費用がかかる**。**成功するまで何度も回さない**——失敗したらログで原因を特定してから再実行する。

---

## ステップ4.5：テストスイートの実行

```powershell
cd C:\Users\gimatakumi\Documents\projects\NBA_news\app\backend
python -c "import os; print('DATABASE_URL' in os.environ)"
```

**期待：`False`**（🔴 ステップ2.5 の後片付けができているか。`True` なら `Remove-Item Env:\DATABASE_URL`）

```powershell
pytest
```

**期待：90 passed**

> **テストDBは SQLite 維持**（テスト設計書§6-4）。`conftest.py` はテスト専用エンジンを自前で生成するため、**`DATABASE_URL` が未設定か SQLite URL のときは**移行後も通る。**接続URL形式の環境変数が残っていると、モジュール import 時の `create_engine()` が先に走って失敗する**（テスト設計書 v0.7 で `conftest.py` にダミー値を足して塞ぐ）。

---

## 第1区の完了判定

| # | 項目 | 判定 |
|---|---|---|
| 0 | Auto-Deploy が `No` | ✅ |
| 1 | Neon プロジェクト作成・**Direct** 接続文字列・**`postgresql+psycopg://`** に書き換え | ✅ |
| 2 | `models.py` 切り替え・push・**Deploys にデプロイが走っていない** | ✅ |
| 2.5 | `pip install`・ローカルから Neon へ `select 1` が通る（`driver: psycopg`）・**環境変数を消した** | ✅ |
| 3 | Secrets **3件のみ**（認証系3件が無い） | ✅ |
| 4 | ジョブ成功・**`INFO` ログあり**・**`articles` > 0**・**`users` = 0** | ✅ |
| 4.5 | `pytest` 90 passed | ✅ |

> 🟢**ここまでは本番無傷である。** 全項目に ✅ が付いたら、`instruction_7-A-10.md` の**第2区（5A・5B・5C）**へ進む。第2区も後戻りできる。
>
> 🔴**後戻り限界点は第3区**である。そこに入る前に、**`total_articles` の照合**（現在 358）を済ませる。
