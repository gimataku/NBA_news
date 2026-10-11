# 実装指示文：7-A-3 ステータスAPI拡張（運用指標）

- **対象**: フェーズ3 手順7 サブ手順 7-A-3
- **作成日**: 2026-10-11
- **設計**: 詳細設計書 v0.4 §2-2-1・§2-1-3・§1-1-3・§4-1／基本設計書 v0.8 §6-1／要件定義書 v0.6 §4-1
- **位置づけ**: **クリティカルパス**。7-A-10（移行・期限 2026-10-19）**より先に完了させる**

> **なぜ移行より先か**: 中止基準「データ消失」（要件定義書§3-3-2 項目5）は、**指標1（総記事数）・指標2（直近7日の取得件数）の急減として検知する**設計である。移行を先に行うと**検知手段がない状態で移行する**ことになる。

---

## 0. 作業範囲と禁止事項

**変更するファイルは4つだけ。**

| # | ファイル |
|---|---|
| 1 | `backend/config.py` |
| 2 | `backend/db/crud.py` |
| 3 | `backend/api/routes.py` |
| 4 | `frontend/src/hooks/useNews.js` |

**🔴 後続サブ手順の定数を先行して追加してはならない。**

| 定数 | 担当サブ手順 |
|---|---|
| `LOGIN_RATE_LIMIT` | 7-A-4 |
| `CORS_ALLOW_METHODS` / `CORS_ALLOW_HEADERS` | 7-A-5 |
| `ENABLE_SCHEDULER` | 7-A-9 / 7-A-10 |

**🔴 テストコードは書かない。** T-P3-03（TC-03-1〜8）の作成は**手順8**である（テスト設計書 v0.6 §0-3）。本サブ手順の検証は§5の手動確認で行う。

**🔴 `.env` を読み取ってはならない。** `cat` / `head` / `tail` / `grep` / `wc` / `od` / `xxd` / `strings` / `source` のいずれも `.env` に対して実行しない。

---

## 1. `backend/config.py`

**L29 `DATA_RETENTION_DAYS = 30` の直後に追加する。**

```python
# データ保持
DATA_RETENTION_DAYS = 30

# 運用指標（/api/status の metrics 集計期間）
METRICS_WINDOW_DAYS = 7   # 週次チェックリストの周期と一致させる
```

> **N=7 の根拠**: 基本設計書§6-1。週次チェックリストの周期と一致させる。

---

## 2. `backend/db/crud.py`

### 2-1. import の変更（2行のみ）

```python
# L3（変更前）
from sqlalchemy import desc
# L3（変更後）
from sqlalchemy import desc, func

# L5（変更前）
from config import DATA_RETENTION_DAYS
# L5（変更後）
from config import DATA_RETENTION_DAYS, METRICS_WINDOW_DAYS
```

**L1 `from datetime import datetime, timedelta, timezone` は既にある。変更しない。**

**L6 `from .models import AppSetting, Article, FetchLog, GameSchedule, SessionLocal, User` は変更しない** —— `FetchLog` は既に import 済みである。

### 2-2. `get_metrics()` をファイル末尾（L207 の後）に追加する

```python
def get_metrics() -> dict:
    """
    /api/status の metrics 用。要件定義書§4-1 の指標1・2・3・6・9 を返す。
    指標7（ERROR件数）・8（Disk使用量）はAPIでは扱わない（基本設計書§6-1）。
    """
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=METRICS_WINDOW_DAYS)
    ).strftime("%Y-%m-%dT%H:%M:%S")

    with SessionLocal() as session:
        total = (
            session.query(func.count(Article.id))
            .filter(Article.is_duplicate == 0).scalar()
        )
        last_7d = (
            session.query(func.count(Article.id))
            .filter(Article.is_duplicate == 0)
            .filter(Article.fetched_at >= cutoff).scalar()
        )
        by_category = dict(
            session.query(Article.category, func.count(Article.id))
            .filter(Article.is_duplicate == 0)
            .filter(Article.fetched_at >= cutoff)
            .group_by(Article.category).all()
        )
        duplicates = (
            session.query(func.count(Article.id))
            .filter(Article.is_duplicate == 1).scalar()
        )
        fallbacks = (
            session.query(func.count(FetchLog.id))
            .filter(FetchLog.is_fallback == 1)
            .filter(FetchLog.executed_at >= cutoff).scalar()
        )

    return {
        "total_articles":      total,
        "articles_last_7d":    last_7d,
        "by_category_7d":      {k: v for k, v in by_category.items() if k is not None},
        "duplicate_count":     duplicates,
        "fallback_history_7d": fallbacks,
    }
```

### 2-3. 守るべき実装上の制約

| # | 制約 | 根拠 |
|---|---|---|
| 1 | **`with SessionLocal()` を1つにまとめ、5クエリをその中で実行する** | 接続の確立を1回に抑える。要望1採用時（Neon・CU課金）に効く |
| 2 | **`func.count()` による集計クエリにする**。全件を Python 側に取り出して `len()` で数えない | 記事数の増加でメモリと転送量が増える |
| 3 | **生SQLを使わない** | `crud.py` は全関数が SQLAlchemy ORM（生SQL 0件）。移行時の変更を1行に抑える方針（基本設計書§5）を崩さない |
| 4 | **日時比較は文字列のまま**（`fetched_at >= cutoff`） | `fetched_at`・`executed_at` は TEXT カラム。ISO8601 は辞書順と時系列順が一致する。**カラム型を変えない** |

### 2-4. 🔴 最も間違えやすい点：NULL 除外の非対称性

| 項目 | `category = NULL` の記事 |
|---|---|
| `by_category_7d` | **除外する**（`if k is not None`） |
| `articles_last_7d` | **含める** |

**この非対称が仕様である。** `category` は翻訳失敗時に NULL になる。キーが `null` の項目は JSON で扱いづらくカテゴリ分布の読み取りを妨げるため `by_category_7d` から除くが、**件数自体は `articles_last_7d` に含め、差分から翻訳失敗の件数を把握できるようにする**（詳細設計書§2-2-1）。

> **`articles_last_7d` にも NULL 除外を適用してはならない。** 適用すると **`by_category_7d` の合計と `articles_last_7d` が一致するようになり、一見正しく見える**。**合計が一致しないことが正しい。**

---

## 3. `backend/api/routes.py`

**L100 `"api_limit_exceeded": ...` の直後に1行追加する。**

```python
@router.get("/status")
async def get_status(current_user: str = Depends(get_current_user)):
    log = crud.get_latest_fetch_log()
    return {
        "last_fetched_at":    crud.get_setting("last_fetched_at"),
        "source_used":        log["source_used"] if log else None,
        "is_fallback":        log["is_fallback"] if log else False,
        "api_limit_exceeded": crud.get_setting("api_limit_exceeded") == "true",
        "metrics":            crud.get_metrics(),                       # 追加
    }
```

| # | 制約 | 根拠 |
|---|---|---|
| 1 | **既存4項目のキー名・順序・意味を変更しない** | 週次チェックリストと `useNews.js` が参照している |
| 2 | **`metrics` オブジェクト1つとして追加する**（フラットに5キー増やさない） | 既存と新規の境界を明示し、フロント側で `metrics == null` の分岐を書けるようにする |
| 3 | 🔴**`try/except` で囲まない。`metrics: null` を返さない** | 詳細設計書§4-1：集計失敗は**握りつぶさない**。`/api/status` 全体が500になるのが正しい。**`metrics: null` を返すと、週次チェックリストで「指標が取れない」ことに気付けない**。`/api/status` は監視の入口であり、**壊れていることが見えるべき**である |
| 4 | **`Depends(get_current_user)` はそのまま。JWT 必須を維持する** | 基本設計書§6-1：記事件数・カテゴリ分布は利用実態を推測できる |

---

## 4. `frontend/src/hooks/useNews.js`

**L13-17 の初期値に1行追加する。**

```javascript
const [apiStatus, setApiStatus] = useState({
  api_limit_exceeded: false,
  is_fallback: false,
  last_fetched_at: null,
  metrics: null,          // 追加。未取得・旧APIのときは null
});
```

**L51 `setApiStatus(status)` は変更しない。戻り値（L103 以降）にも手を入れない。**

> **`metrics` を画面に出すのは本フェーズの要件ではない**（詳細設計書§1-1-3）。要件定義書§4-1 の運用指標は**週次チェックリストでの確認**が用途であり、`/api/status` を直接叩いて読む。**フックが受け取って保持するところまで**が本サブ手順の範囲である。

---

## 5. 検証

| # | コマンド／操作 | 期待結果 |
|---|---|---|
| 1 | `python -c "import config; print('OK')"` | 成功 |
| 2 | `python -c "from db import crud; print(hasattr(crud, 'get_metrics'))"` | `True` |
| 3 | `python -c "import main"` | 成功 |
| 4 | `pytest` | **90 passed**（回帰なし。T-P3-03 は手順8で追加するため件数は増えない） |
| 5 | `npm run lint`（`frontend/`） | エラーなし |
| 6 | ローカル起動 → ログイン → `GET /api/status` | **既存4キー＋`metrics`**。`metrics` 内は**5キー**（`total_articles`・`articles_last_7d`・`by_category_7d`・`duplicate_count`・`fallback_history_7d`） |
| 7 | #6 のレスポンス | **`by_category_7d` の値の合計 ≦ `articles_last_7d`**。一致しない場合、差が `category=NULL`（翻訳失敗）の件数 |

> **#7 が §2-4 に対応する確認である。** 合計が `articles_last_7d` と**完全に一致していたら、NULL 除外を `articles_last_7d` にも適用してしまっている**可能性がある。コードを見直す。
>
> **⚠️ 報告に含めてよいもの**: コマンドの成否、`pytest` の件数、`/api/status` のキー構成、**`metrics` の各数値**（件数のみ）。
>
> **⚠️ 報告に含めてはならないもの**: **JWT トークン**・記事タイトル・記事要約・環境変数の値。

---

## 6. 完了後に報告する項目

| # | 項目 |
|---|---|
| 1 | §1〜§4 の変更が設計書どおりか（**行番号を添えて**） |
| 2 | §5 の検証7件の結果 |
| 3 | 🔴**`total_articles` と `articles_last_7d` の実値** |

> **#3 は 7-A-10（移行）での「データ消失＝急減」判定の基準値になる**（計画書 実装順序の制約#2）。**移行の直前にもう一度取り直すが、この時点の値を製造検証ログに残す。**
