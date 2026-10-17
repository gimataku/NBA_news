# 実装指示 7-A-5：F-18・F-19・F-21 ＋ `cors_client` フィクスチャ

作成日：2026-10-17 ／ 主担当：Claude Code（実装）→ Takumi様（commit・push・本番確認）
設計：詳細設計書 v0.4 §2-1-2（F-18）・§2-3（F-19）・§2-4-1・§2-6（F-21）／基本設計書 v0.8 §4-2・§4-3・§4-5／テスト設計書 v0.6 T-P3-02・T-P3-04・T-P3-05
前提：✅ 7-A-1・3・4・9・10・11・12 完了。本番は Neon ＋ Render 無料プラン。`pytest` 112 passed

> **3件の概要**：F-18 `/api/schedule` の日付を `date` 型で検証する（不正値は 422）／F-19 非推奨の `datetime.utcnow()` を置換する／F-21 CORS の `allow_methods`・`allow_headers` を `["*"]` から実使用の値に限定する。

---

## 0. 作業範囲と禁止事項

### 0-1. 変更するファイル

| # | ファイル | 種別 | 内容 |
|---|---|---|---|
| 1 | `backend/api/routes.py` | 変更 | F-18 |
| 2 | `backend/auth/jwt.py` | 変更 | F-19（本番側） |
| 3 | `backend/tests/test_routes.py` | 変更（**1行のみ**） | F-19（テスト側 L119） |
| 4 | `backend/config.py` | 変更（2定数） | F-21 |
| 5 | `backend/main.py` | 変更 | F-21 |
| 6 | `backend/tests/conftest.py` | 変更 | `cors_client` フィクスチャの追加 |
| 7 | `backend/tests/test_schedule_date.py` | **新規** | T-P3-02（TC-02-1〜6） |
| 8 | `backend/tests/test_jwt_token.py` | **新規** | T-P3-04（TC-04-1〜4） |
| 9 | `backend/tests/test_cors.py` | **新規** | T-P3-05（TC-05-1〜11） |

### 0-2. 禁止事項（🔴厳守）

- **`.env` を読まない**。シークレット・接続文字列を出力しない。
- **F-17（レートリミット）・`limiter.py`・`main.py` の `app.state.limiter` 周りに触れない**（7-A-4 の成果。キー関数は変更しない）。
- **`crud.py` を変更しない**（F-18 は API 層で `.isoformat()` に戻す。内側の層は変更しない）。
- **`datetime.utcnow()` の置換は `auth/jwt.py` と `tests/test_routes.py` L119 の2箇所のみ**。`monitor.py` L149 の `datetime.now()`（naive）は `utcnow()` ではなく本件の範囲外。
- **`ALLOWED_ORIGINS` の扱いを変えない**（`allow_origins`・`allow_credentials` は変更しない）。
- **`test_crud.py` の `test_t10` など既存テストを変更しない**（既知の不安定さは別件）。
- **実バッチ・外部 API・本番へのリクエストを実行しない。**
- **`render.yaml`・`batch.yml`・フロントエンドは変更しない。**

### 0-3. テストの前倒し

7-A-4 と同じ理由（実装と同じサブ手順で触る・セキュリティ関連）で、T-P3-02・T-P3-04・T-P3-05 を**本サブ手順で実装する**（手順8 の前倒し）。**T-P3-04 の TC-04-5（`utcnow` が残っていないこと）は pytest のテストにせず、§5 の `grep` で確認する**（静的検査・設計書の指定どおり）。

---

## 1. F-18：`backend/api/routes.py`

現状（L84-92）：

```python
@router.get("/schedule")
async def get_schedule(
    start_date: str,
    end_date: str,
    current_user: str = Depends(get_current_user),
):
    """C-05タブ用。game_scheduleテーブルから試合日程を返す。"""
    games = crud.get_game_schedule(start_date, end_date)
    return {"games": games}
```

変更後：

```python
@router.get("/schedule")
async def get_schedule(
    start_date: date,
    end_date: date,
    current_user: str = Depends(get_current_user),
):
    """C-05タブ用。game_scheduleテーブルから試合日程を返す。"""
    games = crud.get_game_schedule(start_date.isoformat(), end_date.isoformat())
    return {"games": games}
```

1. ファイル先頭（L1 の `from fastapi import ...` の**前**）に `from datetime import date` を追加し、標準ライブラリとサードパーティの間に空行を置く（既存のスタイルに合わせる）。
2. **`.isoformat()` を忘れない**（`GameSchedule.game_date` は TEXT。`date` オブジェクトのまま渡すと PostgreSQL で型不一致になる）。
3. **`start_date > end_date` の検証は行わない**（空配列が返るだけ。設計§2-1-2）。
4. フロント（`GameSchedule.jsx` L9-11）は `toISOString().split('T')[0]` で `YYYY-MM-DD` を送っているため、**変更後も表示は変わらない**（確認済み）。

---

## 2. F-19：`utcnow()` の置換

### 2-1. `backend/auth/jwt.py`

- L1：`from datetime import datetime, timedelta` → **`from datetime import datetime, timedelta, timezone`**
- **L16**（設計書は L11 と記すが、7-A-1 の変更で位置が動いた。**実測の L16**）：
  ```python
  # 変更前
  expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
  # 変更後
  expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
  ```
- python-jose は `datetime` の `exp` を UTC のエポック秒（整数）に変換するため、**発行されるトークンの `exp` の値は変わらない**。既存トークンも引き続き有効。

### 2-2. `backend/tests/test_routes.py` L119

```python
# 変更前
"exp": datetime.utcnow() - timedelta(hours=1),
# 変更後
"exp": datetime.now(timezone.utc) - timedelta(hours=1),
```

- `test_routes.py` L4 は既に `from datetime import datetime, timezone` を import 済み（`timedelta` は L111 でローカル import 済み）。**import の変更は不要**。**この1行以外は変更しない。**

---

## 3. F-21：CORS の限定

### 3-1. `backend/config.py`

`LOGIN_RATE_LIMIT` の直後に追加する（`ENABLE_SCHEDULER` は追加しない＝7-A-10c で `main.py` に実装済み）。

```python
# CORS設定（F-21）：main.py とテストフィクスチャの双方がここを読む（乖離させない）
CORS_ALLOW_METHODS = ["GET", "POST", "PUT"]
CORS_ALLOW_HEADERS = ["Authorization", "Content-Type"]
```

- **`PUT` を落とさない**（`useNews.js` が `PUT /api/settings` を呼ぶ。落とすとネタバレ防止トグルとチームフィルタが保存できなくなる）。
- 使用メソッドの確認結果：`GET`（news・status・schedule・settings）・`POST`（auth/login）・`PUT`（settings）。`DELETE`／`PATCH` は使用なし。使用ヘッダ：`Authorization`・`Content-Type` のみ（`useNews.js`・`useAuth.js`・`GameSchedule.jsx` で確認済み）。

### 3-2. `backend/main.py`

1. import を追加（既存のスタイルに合わせる）：`from config import CORS_ALLOW_HEADERS, CORS_ALLOW_METHODS`
2. `app.add_middleware(CORSMiddleware, ...)` を次のとおり変更する（**`allow_origins`・`allow_credentials` は変更しない**）：
   ```python
   allow_methods=CORS_ALLOW_METHODS,
   allow_headers=CORS_ALLOW_HEADERS,
   ```
3. `app.state.limiter`・`_scheduler_enabled()`・`uvicorn.run` は変更しない。

---

## 4. テスト

### 4-1. `backend/tests/conftest.py`：`cors_client` フィクスチャの追加

`raw_api_client` の後に追加する。**値を書かず `config` の定数を読む**（本番と同じ定数を使う。値を直書きすると回帰テストが機能しない）。`api_client` と同様に `app.state.limiter` とハンドラも設定する。

```python
@pytest.fixture
def cors_client(reset_db):
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.testclient import TestClient
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from api.limiter import limiter
    from api.routes import get_current_user, router
    from config import CORS_ALLOW_HEADERS, CORS_ALLOW_METHODS

    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_current_user] = lambda: "testuser"
    with TestClient(app) as client:
        yield client
```

### 4-2. `backend/tests/test_schedule_date.py`（新規・T-P3-02）

`api_client`（認証オーバーライドあり）を使う。`game_schedule` へのデータ投入は、**`tests/test_routes.py` L215-250 付近・`tests/test_integration.py` L110-125 付近の既存パターンに揃える**。

| ケース | 入力 | 期待 |
|---|---|---|
| TC-02-1 | `start_date=2026-09-01&end_date=2026-09-07` | 200・**期間内の試合のみ**返る（期間外の行も投入しておく） |
| TC-02-2 | `start_date=2026-13-01`（月が不正） | **422** |
| TC-02-3 | `start_date=abc` | **422** |
| TC-02-4 | `start_date` を省略 | **422** |
| TC-02-5 | `start_date=2026-09-07&end_date=2026-09-01`（逆転） | **200・空配列** |
| **TC-02-6** | `game_date` が `start_date` と**完全一致**・`end_date` と**完全一致**の2行 | **両方とも含まれる**（`>=` / `<=`。`.isoformat()` の検証を兼ねる） |

### 4-3. `backend/tests/test_jwt_token.py`（新規・T-P3-04）

| ケース | 操作 | 期待 |
|---|---|---|
| TC-04-1 | `create_access_token({"sub": "u"})` → `verify_token()` | `"u"` |
| TC-04-2 | `exp` を過去にしたトークンを `verify_token()`（`datetime.now(timezone.utc) - timedelta(hours=1)`・`jose.jwt.encode`） | `None` |
| TC-04-3 | 発行直後のトークンを復号して `exp` を確認 | **現在時刻＋`ACCESS_TOKEN_EXPIRE_DAYS` 日（±10秒）**（日数は `config` から導く。30 を直書きしない） |
| TC-04-4 | 改ざんしたトークン | `None` |

> **TC-04-5（`utcnow` の残存なし）は §5 の `grep` で確認する**。テストファイルにも `utcnow` の文字列を書かない。

### 4-4. `backend/tests/test_cors.py`（新規・T-P3-05）

`cors_client` を使う。許可オリジンは `http://localhost:5173`（フィクスチャの `allow_origins`）。プリフライトは `client.options("/api/settings", headers={...})`。

**Starlette の `CORSMiddleware` の挙動**：許可されないメソッド・ヘッダ・オリジンのプリフライトは **HTTP 400** を返す（本文 `Disallowed CORS method/headers/origin`）。許可されるときは **200**。したがって「許可」「拒否」は次のように検証する。

| ケース | プリフライト | 期待 |
|---|---|---|
| TC-05-1 | `Origin: http://localhost:5173`／`Access-Control-Request-Method: GET` | **200**・`Access-Control-Allow-Methods` に `GET` |
| TC-05-2 | 同／`POST` | **200**・`POST` を含む |
| **TC-05-3** | 同／**`PUT`** | **200**・`PUT` を含む（基本設計書 v0.6 の値では落ちた。回帰） |
| TC-05-4 | 同／`DELETE` | **400**・`Allow-Methods` に `DELETE` を含まない |
| TC-05-5 | 同／`PATCH` | **400**・`PATCH` を含まない |
| TC-05-6 | `Access-Control-Request-Method: PUT`／`Access-Control-Request-Headers: Authorization` | **200** |
| TC-05-7 | 同／`Content-Type` | **200** |
| TC-05-8 | 同／`X-Custom-Header` | **400** |
| TC-05-9 | `Origin: https://evil.example` | **`Access-Control-Allow-Origin` が返らない**（400） |
| **TC-05-10** | **実リクエスト** `PUT /api/settings`（`Origin: http://localhost:5173`・JSON 本文） | **200**・`Access-Control-Allow-Origin` が返る |
| **TC-05-11** | `import main` して `app.user_middleware` を検査（**`TestClient` を使わない**） | `CORSMiddleware` の `kwargs["allow_methods"]` が **`config.CORS_ALLOW_METHODS` と一致**。`allow_headers` も同様 |

TC-05-11 の実装（テスト設計書 T-P3-05）：

```python
def test_main_cors_options_match_config():
    import main
    from config import CORS_ALLOW_HEADERS, CORS_ALLOW_METHODS
    mw = next(m for m in main.app.user_middleware if m.cls.__name__ == "CORSMiddleware")
    assert mw.kwargs["allow_methods"] == CORS_ALLOW_METHODS
    assert mw.kwargs["allow_headers"] == CORS_ALLOW_HEADERS
```

- **`Middleware.kwargs` の属性名は Starlette の版に依存する**（テスト設計書 §9 #15）。**インストール済みの版で属性が実在するか最初に確認し、違えば合わせて報告する**。
- `import main` は安全（`scheduler.start()` は `startup_event()` 内のみ。`os.makedirs("logs")` の副作用だけ）。**`test_main_scheduler.py` が既に `import main` している。**
- TC-05-4・5・8・9 の 400 はミドルウェアの仕様に基づく。**実際の挙動が異なる場合は、仕様のほうに合わせて期待値を直し、差異を報告する**（期待値を緩めて通すことはしない）。

---

## 5. 検証（Claude Code）

| # | 確認 | 期待 |
|---|---|---|
| 1 | `Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue` の後に `pytest` | **全件 passed**（112 ＋ T-P3-02 の6 ＋ T-P3-04 の4 ＋ T-P3-05 の11 ＝ **133 passed** 想定。件数と**警告の件数**を報告。`utcnow()` 由来の `DeprecationWarning` が減るはず） |
| 2 | **TC-04-5**：`grep -rn "utcnow" backend/ --include=*.py` | **0 件** |
| 3 | `grep -n 'allow_methods=\["\*"\]\|allow_headers=\["\*"\]' backend/main.py` | **0 件** |
| 4 | `grep -n "CORS_ALLOW" backend/main.py backend/config.py backend/tests/conftest.py` | `config.py`（定義）・`main.py`（import・使用）・`conftest.py`（import・使用）。**値の直書きが `config.py` 以外に無い** |
| 5 | `python -c "from api.routes import router; print(sorted(r.path for r in router.routes))"` | ルートの増減なし（`/auth/login`・`/news`・`/schedule`・`/settings`×2・`/status`） |
| 6 | `git diff --stat` | §0-1 の9ファイルのみ（新規3）。**`.env`・`render.yaml`・`batch.yml`・フロントを含まない**。**`test_routes.py` の差分が1行** |

---

## 6. 報告

1. pytest の件数と警告の件数。
2. 検証 #2〜#6 の結果。
3. 変更後の `routes.py` の `get_schedule`、`jwt.py` の import と `create_access_token`、`main.py` の CORS 部分、`config.py` の追加分。
4. 設計書との差異（`jwt.py` の行番号 L11→L16、TC-05 の期待値が 400 であること、`Middleware.kwargs` の確認結果 等）。
5. commit は Takumi様が確認してから。

---

## 7. 本番確認（Takumi様・push 後）

**デプロイ成功後、ブラウザで次を確認する**（CORS の実ブラウザでの挙動は自動テストでは担保できない。テスト設計書 §9 #13）。

| # | 確認 | 期待 |
|---|---|---|
| 1 | ログインする | 成功（`POST`＋`Content-Type`） |
| 2 | ニュース一覧・ステータスが表示される | 表示される（`Authorization`） |
| 3 | **ネタバレ防止トグル・チームフィルタを切り替え、ページを再読込する** | 設定が保存されている（**`PUT /api/settings` が CORS を通る**＝F-21 の `PUT` 回帰） |
| 4 | 試合日程タブ | 日程または「試合日程がありません」が出る（エラーなし。F-18 の日付形式 `YYYY-MM-DD`） |
| 5 | ブラウザの開発者ツールのコンソール | **CORS エラーなし** |

PowerShell でのプリフライト確認（任意）：

```powershell
$u = "https://nba-news-backend-ppsd.onrender.com/api/settings"
$origin = "https://nba-news-frontend.onrender.com"
foreach ($m in "PUT","DELETE") {
  try {
    $r = Invoke-WebRequest -Method Options -Uri $u -Headers @{ "Origin" = $origin; "Access-Control-Request-Method" = $m } -UseBasicParsing
    "$m -> $($r.StatusCode) allow-methods: $($r.Headers['Access-Control-Allow-Methods'])"
  } catch { "$m -> " + [int]$_.Exception.Response.StatusCode }
}
```

期待：`PUT -> 200 allow-methods: GET, POST, PUT`、`DELETE -> 400`。

報告してほしいのは：確認 1〜5 の可否（特に **3**）と、PowerShell を実行した場合はその出力。
