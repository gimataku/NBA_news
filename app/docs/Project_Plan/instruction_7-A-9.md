# 実装指示文：7-A-9 移行用の新規成果物の作成

- **対象**: フェーズ3 手順7 サブ手順 7-A-9
- **作成日**: 2026-10-11
- **設計**: 詳細設計書 v0.4 §3-1・§3-1-1・§3-3・§3-4・§2-7／基本設計書 v0.8 §5-2・§5-7・§6-2-2
- **位置づけ**: **クリティカルパス**。7-A-10（移行・期限 2026-10-19）**より先に完了させる**
- **前提**: 7-A-1（先-1 `config.py` の用途別分離）が ✅完了していること ── **本サブ手順はその成果に依存する**

---

## 0. 🔴 作業を2つに分ける（`.github/` は連携フォルダの外にある）

**`.github/workflows/batch.yml` はリポジトリルート（`NBA_news/.github/`）に置かれる。** GitHub Actions はワークフローファイルを**リポジトリルートの `.github/workflows/`** からしか読まない。本プロジェクトは `app/` の1つ上がリポジトリルートであるため、**`app/` の外**になる。

| ブロック | 対象 | 担当 | 理由 |
|---|---|---|---|
| **7-A-9a** | `backend/run_batch_once.py`（新規）・`backend/db/models.py`・`backend/requirements.txt` | **Claude Code** | いずれも `app/` 配下 |
| **7-A-9b** | `../.github/workflows/batch.yml`（新規） | 🔴**Takumi様**（手で作成） | **`app/` の外**。Claude Code のプロジェクトルートも `app/` であり、**ルート外への書き込みになる** |

> **⚠️ Claude Code に `../.github/` を書かせない。** 承認を求められるか拒否されるかはさておき、**プロジェクトルートの外へ書く操作をバッチ作業の中に混ぜない**方がよい。§3 に全文を載せてあるので、**Takumi様がそのまま貼り付けて作成する**。

---

## 1. 🔴 作業範囲と禁止事項

**7-A-9a で変更するファイルは3つだけ。**

| # | ファイル | 操作 |
|---|---|---|
| 1 | `backend/run_batch_once.py` | **新規作成** |
| 2 | `backend/db/models.py` | L82-83 を変更 |
| 3 | `backend/requirements.txt` | 1行追加 |

**🔴 後続・他サブ手順のものを先行して追加してはならない。**

| もの | 担当サブ手順 |
|---|---|
| `slowapi`（`requirements.txt`） | **7-A-4**（F-17）。**本サブ手順では追加しない** |
| `LOGIN_RATE_LIMIT` / `api/limiter.py` | 7-A-4 |
| `CORS_ALLOW_METHODS` / `CORS_ALLOW_HEADERS` | 7-A-5 |
| **`ENABLE_SCHEDULER` と `main.py` の3分岐** | **7-A-10**（移行の実行と同時）。**本サブ手順では触らない** |
| `/api/fetch` の削除 | 7-A-11（**7-A-10 の後**） |

**🔴 テストコードは書かない。** T-P3-15（TC-15-1〜7）・T-P3-16（TC-16-1〜6）の作成は**手順8**である（テスト設計書 v0.6 §0-3）。本サブ手順の検証は§5の手動確認で行う。

**🔴 `.env` を読み取ってはならない。** `cat` / `head` / `tail` / `grep` / `wc` / `od` / `xxd` / `strings` / `source` のいずれも `.env` に対して実行しない。

**🔴 `render.yaml` を触ってはならない。** Blueprint 連携下にあり、**sync が走ると Auto-Deploy Off でも止められない可能性がある**（7-A-0 帰結#3）。構成変更は 7-A-10 にまとめる。

---

## 2. 7-A-9a-1：`backend/run_batch_once.py`（新規）

詳細設計書§3-1 のコードブロックに、**`logging.basicConfig()` の1行を加えたもの**を実装する。追加の根拠は§2-3 を参照。

```python
"""GitHub Actions から起動する1回限りのバッチ実行スクリプト。
APScheduler を介さず、run_batch() と run_game_schedule_batch() を直接呼ぶ。
"""
import logging
import os
import sys

import requests

from db import crud
from db.models import init_db
from scheduler import run_batch, run_game_schedule_batch

# GitHub Actions のログに進行状況を残す（詳細設計書§3-3 の注記「標準出力のみ」を実現する）
# ファイル出力は設定しない（logs/ を作らない。os.makedirs は main.py にしかない）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


def main() -> int:
    # ① スキーマの用意（基本設計書§5-2：移行手順4のために必須。冪等）
    init_db()

    # ② 記事取得
    run_batch()

    # ③ 試合日程取得
    run_game_schedule_batch()

    # ④ 成否判定（基本設計書§5-2 案A・§8 #13）
    log = crud.get_latest_fetch_log()
    if log is None or log["error_message"] is not None:
        logger.error("batch failed: %s", log["error_message"] if log else "no fetch_log")
        return 1                      # ← ping せず非ゼロ終了

    # ⑤ ping（判定に合格した場合のみ。基本設計書§6-2-2）
    url = os.getenv("HEALTHCHECK_PING_URL")
    if url:
        try:
            requests.get(url, timeout=10)
        except Exception as exc:
            logger.warning("healthcheck ping failed: %s", exc)   # pingの失敗で落とさない
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 2-1. 守るべき実装上の制約

| # | 制約 | 根拠 |
|---|---|---|
| 1 | **`init_db()` を先頭で呼ぶ** | 移行手順4の時点で、**Neon にテーブルを作る主体が他にいない**。冪等（`create_all` ＋ `session.get` での存在確認） |
| 2 | 🔴**`init_user()` は呼ばない** | バッチは認証を使わない。**呼ぶと 7-A-1（先-1）の目的が崩れ、GitHub Secrets に認証系3件を入れる必要が生じる** |
| 3 | **`check_and_run_batch()` / `check_and_run_*` は呼ばない** | 4時間ゲートを外す。cron 側で間隔を決める |
| 4 | **`run_batch()` → `run_game_schedule_batch()` の順** | §3-1 |
| 5 | **成否判定は③の後・⑤の前** | 判定に使う `fetch_log` は②で書かれるため③の後でも値は変わらないが、**「全部走らせてから判定する」方が意図が伝わる** |
| 6 | 🔴**`log is None` も失敗として扱う**（`return 1`） | `run_batch()` は成功・失敗いずれでも `save_fetch_log()` を呼ぶ（`scheduler.py` L63・L171）。**`None` は `save_fetch_log()` に到達しなかったことを意味する**＝例外は出ていないが異常 |
| 7 | 🔴**`try/except` で全体を囲まない** | DB障害は**未捕捉のまま伝播**させ、Python 既定の非ゼロ終了にする（§4-1） |
| 8 | 🔴**ping の失敗で終了コードを変えない**（`warning` ログのみ） | **バッチの失敗と監視の失敗を混同すると、原因の切り分けができなくなる**。ping サービスの一時障害でジョブが赤くなってはならない |
| 9 | **`HEALTHCHECK_PING_URL` 未設定ならスキップ**（例外にしない） | バッチの目的に必須ではない。`config.py` の必須チェックに加えない |
| 10 | **`HEALTHCHECK_PING_URL` は `os.getenv()` で直接読む。`config.py` に置かない** | この値は**このスクリプトでしか使わない**。`config` を import する全モジュールが知る必要のない設定を抱えることになる（§3-2 の用途別分離と一貫させる） |
| 11 | **`logging.FileHandler` を設定しない** | `os.makedirs("logs", exist_ok=True)` は `main.py` L15 にしかない。**`run_batch_once.py` は `main.py` を import しない**ため、ファイル出力を設定すると `logs/` が無い環境で落ちる |

### 2-2. 失敗4種と期待される挙動（§3-1-1）

| # | 失敗 | 終了コード | ping |
|---|---|---|---|
| 1 | RSS全ソース失敗 | **1** | ❌しない |
| 2 | 試合日程取得の失敗 | 0 | ✅する（**意図的に検知対象外**） |
| 3 | Claude API の RateLimit | 0 | ✅する（**週次チェックリストで `api_limit_exceeded` を確認**） |
| 4 | DB接続失敗 | **1** | ❌しない |

> **#2・#3 を検知対象にしないのは基本設計書§5-2 で確定済みである。本サブ手順で扱いを変えない。**

### 2-3. ⚠️ `logging.basicConfig()` を加える根拠（設計書のコードブロックには無い）

**詳細設計書§3-3 の注記は「`run_batch_once.py` はファイル出力を設定せず、標準出力のみとする（GitHub Actions のログに残るため、ファイルに書く必要がない）」と述べている。しかし §3-1 のコードブロックには、標準出力に出すための設定が無い。**

| 状態 | 挙動 |
|---|---|
| `basicConfig()` なし（§3-1 のコードブロックのまま） | root logger にハンドラが無いため **`logging.lastResort`（stderr・WARNING 以上）** が処理する。**`logger.error`（batch failed）と `logger.warning`（ping failed）は出るが、`scheduler.py` の `logger.info` は全部消える** |
| `basicConfig(level=INFO, stream=stdout)` あり | **取得件数・フォールバックの有無・試合日程の件数などの進行状況が GitHub Actions のログに残る** |

> **なぜ重要か**: 移行後、**このスクリプトが記事取得の唯一の経路になる**（`/api/fetch` は 7-A-11 で削除・Render 側は `ENABLE_SCHEDULER=false`）。**1日6回、無人で走る。** 失敗したときに手がかりが「batch failed: <メッセージ>」の1行しかないのと、進行状況が残っているのとでは、切り分けの速さが大きく違う。
>
> **設計との関係**: これは**設計への反論ではなく、§3-3 の注記が述べた意図を実現するための1行**である。**注記が「こうする」と書いている事項が、コードブロックで実現されていない**——レビュー観点2-9（例示コードと、それを説明する注記・表の整合／**実装者はコードブロックに従う**）が指す形そのものであり、DD2-01 と同じ構図である。
>
> **⚠️ 詳細設計書への反映が必要**。本サブ手順では上記のとおり実装し、**§3-1 のコードブロックへの反映は詳細設計書 v0.5 で行う**（7-A-13 のドキュメント追従更新に含めず、**独立に処理する**——コードブロックの誤りは体裁ではない）。

---

## 3. 7-A-9b：`.github/workflows/batch.yml`（新規・🔴 Takumi様が手で作成）

**配置先**: `C:\Users\gimatakumi\Documents\projects\NBA_news\.github\workflows\batch.yml`（**`app/` の1つ上**）

```yaml
name: NBA News Batch

on:
  schedule:
    - cron: '0 21,1,5,9,13,17 * * *'    # UTC → JST 6/10/14/18/22/2時
  workflow_dispatch:                    # 手動実行（/api/fetch の代替）

jobs:
  run-batch:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: pip
      - run: pip install -r app/backend/requirements.txt
      - name: Run batch
        working-directory: app/backend
        env:
          ANTHROPIC_API_KEY:    ${{ secrets.ANTHROPIC_API_KEY }}
          BALLDONTLIE_API_KEY:  ${{ secrets.BALLDONTLIE_API_KEY }}
          DATABASE_URL:         ${{ secrets.DATABASE_URL }}
          HEALTHCHECK_PING_URL: ${{ secrets.HEALTHCHECK_PING_URL }}
        run: python run_batch_once.py
```

| 項目 | 設計 | 根拠 |
|---|---|---|
| cron 式 | **`0 21,1,5,9,13,17 * * *`（UTC）** | 基本設計書§5-7。JST 6/10/14/18/22/2時 |
| 手動実行 | **`workflow_dispatch`** | 基本設計書§5-4：`/api/fetch` の代替 |
| `working-directory` | **`app/backend`** | 相対 import（`from db import crud`）と `logs/` の作成位置を現行と揃える |
| タイムアウト | **20分** | 通常は数分。無限に回って無料枠（月2000分）を消費しないための上限 |
| 🔴 Secrets | **認証系（`SECRET_KEY`・`USERNAME`・`USER_PASSWORD`）を渡さない** | **7-A-1（先-1）の成果**。`scheduler` の推移的 import 9ファイルに `auth` が無いことを確認済み（7-A-1 コードレビュー観点5） |
| `concurrency` | **設定しない** | 4時間間隔に対し実行は数分。重複起動は起きない |

> **⚠️ `HEALTHCHECK_PING_URL` は 7-A-12（外部cron監視の導入）で決まる。** 未登録のままでも**スクリプト側はスキップする**（§2-1 制約9）ので、**この時点で空でよい**。
>
> **⚠️ cron の遅延**: GitHub Actions の scheduled workflow は**混雑時に数分〜十数分遅れる**。基本設計書§6-2-2 の猶予1時間がこれを吸収する設計である。
>
> **⚠️ 60日無活動での自動無効化**（リスク調査書§1-5 リスク2）は本ファイルでは防げない。**7-A-12 の外部cron監視で検知する。**
>
> **⚠️ GitHub Secrets の登録は 7-A-10 で行う**（実値を扱う作業）。**本サブ手順ではファイルを置くところまで**。登録前に cron が回ると失敗するため、**ファイル作成から 7-A-10 までの間に cron 実行時刻を跨ぐなら、ジョブが失敗する**。これは想定内であり、**7-A-10 完了後の `workflow_dispatch` による手動実行で成功を確認する**。

---

## 4. 7-A-9a-2：`backend/db/models.py`（L82-83 の変更）

```python
# L82-83（変更前）
DB_PATH = os.getenv("DATABASE_URL", "nba_news.db")
engine  = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

# L82-83（変更後）
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///nba_news.db")
engine  = create_engine(DB_PATH, pool_pre_ping=True)
```

**L84 `SessionLocal = sessionmaker(...)` 以降は変更しない。**

| 項目 | 変更前 | 変更後 | 根拠 |
|---|---|---|---|
| `DATABASE_URL` の意味 | **ファイルパス**（`sqlite:///` を後から付けていた） | **接続URL全体** | §3-4 |
| 既定値 | `"nba_news.db"` | **`"sqlite:///nba_news.db"`** | 未設定時にローカル SQLite で動く現行の挙動を維持する |
| `connect_args` | `{"check_same_thread": False}` | **削除** | PostgreSQL では**未知の引数**でエラーになる。SQLAlchemy 2.0 は file-based SQLite にこれを自動付与する |
| 接続の健全性 | なし | **`pool_pre_ping=True`** | **Neon は無操作でコンピュートが休止する**。切れた接続を掴むと最初のクエリが失敗する |

| # | 制約 | 根拠 |
|---|---|---|
| 1 | 🔴**カラム型を `TIMESTAMP` に変えない** | `fetched_at`・`executed_at` は TEXT のまま。**ISO8601 は辞書順と時系列順が一致する**ため PostgreSQL でも `>= cutoff` が正しく動く。変えると `crud.py` の全日時処理が影響を受ける |
| 2 | **`crud.py` は変更しない** | 全関数が SQLAlchemy ORM（生SQL 0件）。**移行で触るのは本1行だけ**という方針（基本設計書§5） |
| 3 | **`tests/conftest.py` は変更しない** | テスト専用エンジンを自前で生成し（L31-35）、`models_module.engine` / `SessionLocal` / `crud_module.SessionLocal` を差し替える（L41-43）。**テストDBは SQLite 維持**（テスト設計書§6-4） |
| 4 | **`sqlalchemy` を 2.0 系から下げない** | 制約の根拠が SQLAlchemy 2.0 の挙動に依存している（§2-7） |

---

## 5. 7-A-9a-3：`backend/requirements.txt`（1行追加）

**L17 `responses` の後に追加する。**

```
psycopg[binary]
```

| # | 制約 | 根拠 |
|---|---|---|
| 1 | 🔴**`slowapi` は追加しない** | §2-7 の表で**採否非依存＝7-A-4（F-17）の担当**。本サブ手順の範囲外 |
| 2 | **バージョンを固定しない** | 既存の記述方針に揃える（`bcrypt<4.0.0` のような制約が必要になった場合のみ付ける） |
| 3 | **`[binary]` を落とさない** | ビルド済みホイールを使う。GitHub Actions でのビルド時間と失敗要因を減らす |

> **⚠️ `psycopg[binary]` を落とすと、GitHub Actions のバッチが初回実行時に接続エラーで落ちる**（詳細設計書 v0.1 がこれを取りこぼし、v0.2 のレビューDD-R-02 で是正された箇所である）。

---

## 6. 検証

**⚠️ Neon への接続はまだ試さない。** 本サブ手順の検証は**ローカル SQLite のまま**で行う。接続先の切り替えは 7-A-10 である。

| # | コマンド／操作 | 期待結果 |
|---|---|---|
| 1 | `python -c "import config"` | 成功 |
| 2 | `python -c "from db.models import engine; print(engine.url.get_backend_name())"` | **`sqlite`**（既定値が効いている＝未設定時の現行挙動を維持） |
| 3 | `python -c "import run_batch_once"` | 成功（**`main()` は走らない**。`if __name__ == "__main__":` で保護されていること） |
| 4 | `pytest` | **90 passed**（回帰なし。`conftest.py` 未変更で通ること＝§4 制約3 の確認） |
| 5 | `python -c "import main"` | 成功 |
| 6 | `grep -n "init_user" run_batch_once.py` | **0件**（§2-1 制約2） |
| 7 | `grep -nE "try:|except" run_batch_once.py` | **ping の1箇所のみ**（§2-1 制約7・8） |
| 8 | `grep -n "slowapi" requirements.txt` | **0件**（§5 制約1） |
| 9 | `pip install -r requirements.txt` を**クリーンな仮想環境**で実行 | 成功（`psycopg[binary]` が解決できること） |
| 10 | `python -c "import psycopg; print(psycopg.__version__)"` | バージョンが出る |
| 11 | **`run_batch_once.py` を実際に実行**（ローカル SQLite・ping 未設定） | **終了コード 0**・**標準出力に `INFO` の進行ログが出る**（§2-3 の確認）・`logs/` が**作られていない** |

> **#11 が本サブ手順で最も重要な確認である。** ここで実際に記事が取得・保存されることを確かめておかないと、**移行後の GitHub Actions 初回実行が最初の実行になる**——**後戻り限界点を越えた後に初めて動かすことになる**。
>
> **⚠️ #11 は Claude API を実際に呼ぶ**（課金が発生する）。実行は**1回だけ**にする。**記事タイトル・要約は共有しない**。報告は**終了コード・ログの行数・`INFO` が出たか否か・保存件数**で足りる。
>
> **⚠️ #11 で `last_fetched_at` が更新される。** 7-A-3 の基準値を取得する前なら、**順序に注意する**（基準値はローカルではなく Render の本番DBから取るため、ローカル実行は影響しない）。

---

## 7. 完了後に報告する項目

| # | 項目 |
|---|---|
| 1 | §2・§4・§5 の変更が設計書どおりか（**行番号を添えて**） |
| 2 | §6 の検証11件の結果 |
| 3 | **#11 の終了コードと、`INFO` ログが標準出力に出たか** |
| 4 | **`logs/` ディレクトリが作られていないこと** |
| 5 | 🔴**7-A-9b（`batch.yml`）を作成したか**（Takumi様の作業） |

---

## 8. 本サブ手順で判明した設計の問題（3件・7-A-10 の前に扱いを決める）

| # | 内容 | 影響 | 対処 |
|---|---|---|---|
| 🟡1 | **§3-1 のコードブロックに `logging.basicConfig()` が無い**（§2-3） | 移行後、**唯一の記事取得経路が無人で1日6回走るのに、進行状況が GitHub Actions のログに残らない** | **本サブ手順で1行追加**。**詳細設計書 v0.5 で §3-1 のコードブロックに反映する** |
| 🔴2 | **`db/migrate_p2.py` L4 も `DATABASE_URL` を読み、ファイルパスとして扱う**（`sqlite3.connect(DB_PATH)`） | 移行後に実行すると **`sqlite3.connect("postgresql+psycopg://...")` となり、その文字列名のファイルを作って「成功」する**——**失敗しないことが最悪である**。§3-4 は「`DATABASE_URL` の意味が変わる」と書いているが、**読んでいる箇所が2つあることに触れていない** | **7-A-10 の前に判断が必要**（下記） |
| 🟢3 | **`requirements.txt` の `sqlalchemy` に下限が無い** | §2-7 は「**2.0 系から下げない**」という制約を述べているが、**それを強制する手段がない**。`connect_args` を削除できる根拠が 2.0 の挙動に依存しているため、1.x が入ると**ローカル SQLite で `check_same_thread` エラーが出る** | **`sqlalchemy>=2.0` と書けば制約が表現できる**。§2-7 の「固定しない」は**上限固定（`==`）を避ける方針**であり、**下限の明示は固定ではない**（`bcrypt<4.0.0` の前例があり、§2-7 自身が「制約が必要になった場合のみ付ける」としている。**§2-7 が制約を述べている以上、該当する**） |

> **🔴2 の選択肢**
>
> | 案 | 内容 | 評価 |
> |---|---|---|
> | **A** | **`migrate_p2.py` の冒頭に「`DATABASE_URL` に `://` が含まれていたら即座に異常終了する」ガードを置く** | ✅**推奨**。3行で済み、**削除の判断を要しない**。「失敗しないことが最悪」を「明示的に失敗する」に変える |
> | B | `migrate_p2.py` を削除する | フェーズ2の移行は適用済みと思われるが、**削除は当方の判断で行わない**。Takumi様の判断 |
> | C | 何もしない（文書に注意を残すだけ） | ❌**採らない**。**注意書きは実行を止めない** |
>
> **⚠️ 案Aを採る場合も、本サブ手順の範囲外とする。** `migrate_p2.py` は移行対象ファイルとして設計書のどの節にも挙がっていない。**7-A-9 に混ぜず、7-A-10 の着手前に別作業として処理する**（11ステップの Blueprint 版書き直しと同じタイミング）。
