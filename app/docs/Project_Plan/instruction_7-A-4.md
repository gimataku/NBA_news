# 実装指示 7-A-4：F-17 ログインのレートリミット ＋ `conftest.py` の改修

作成日：2026-10-15 ／ 主担当：Claude Code（実装）→ Takumi様（commit・push・本番確認）
設計：詳細設計書 v0.4 §2-1-1・§2-4-2・§2-6・§2-7・§4-2-1／基本設計書 v0.8 §4-1／テスト設計書 v0.6 §2-0・T-P3-01・§1-6-2
前提：✅ 7-A-1・7-A-3・7-A-9・7-A-10・7-A-11 完了。本番は Neon（`postgresql+psycopg`）＋ Render 無料プラン

> **なぜ今か**: 公開サイトのログインにブルートフォース対策が無い（フェーズ2はリスク受容）。開幕（2026-10-20）でアクセスが増える前に入れる。

---

## 0. 作業範囲と禁止事項

### 0-1. 変更するファイル（8つ）

| # | ファイル | 種別 |
|---|---|---|
| 1 | `backend/api/limiter.py` | **新規** |
| 2 | `backend/api/routes.py` | 変更 |
| 3 | `backend/main.py` | 変更 |
| 4 | `backend/config.py` | 変更（1定数） |
| 5 | `backend/requirements.txt` | 変更（1行） |
| 6 | `backend/tests/conftest.py` | 変更（§5） |
| 7 | `backend/tests/test_rate_limit.py` | **新規**（T-P3-01・§6） |
| 8 | `frontend/src/hooks/useAuth.js`・`frontend/src/components/LoginForm.jsx` | 変更（§4・429 の UI） |

### 0-2. 禁止事項（🔴厳守）

- **`.env` を読まない**（`cat`／`head`／`tail`／`grep`／`wc`／`od`／`xxd`／`strings`／`source`／dotenv 読み込みのいずれも）。シークレット・接続文字列を出力しない。
- **後続サブ手順の定数・フィクスチャを先行して追加しない**：`CORS_ALLOW_METHODS`／`CORS_ALLOW_HEADERS`／`cors_client`（7-A-5）、`config.ENABLE_SCHEDULER`（`main.py` の `_scheduler_enabled()` で実装済み。設計§2-6 の `config` 定数方式は採らない）。
- **F-18・F-19・F-21 に触れない**（`/schedule` の日付検証・`utcnow()`・CORS）。
- **フロントのテスト（T-P3-14）は書かない**（テスト基盤は 7-A-8。T-P3-14 は 7-A-8 の後）。
- **`config.py` の `load_dotenv()` に `override=True` を付けない**（テスト設計書 §1-6-2 対処5）。
- **実バッチ・外部 API・本番へのリクエストを実行しない。**
- **`render.yaml`・`batch.yml` は変更しない。**

### 0-3. 手順8 の前倒しについて

本リポジトリの慣例は「テストコードは手順8」（7-A-3 は書かなかった）だが、**本サブ手順は T-P3-01 を前倒しで実装する**。理由：①ログインのレート制限はセキュリティ機能であり、`conftest.py` の改修（`reset_rate_limit` 等）の効果を実証する手段が他にない。②`@limiter.limit()` を付けると `app.state.limiter` が無いテスト環境でリクエスト時に例外になる（`conftest.py` の改修が必須）ため、**実装と同じサブ手順で触る**（計画書 §3 の方針）。

---

## 1. `backend/api/limiter.py`（新規）

**インスタンスはここだけで生成する**（`main.py`・`routes.py` は import するだけ。`main` → `routes` → `main` の循環 import を避ける）。

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

---

## 2. `backend/api/routes.py`

現状の先頭（7-A-11 後）：

```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
...
from auth.users import authenticate_user
from db import crud

router = APIRouter()
```

変更：

1. L1 の `from fastapi import ...` に **`Request` を追加**（`BackgroundTasks` は 7-A-11 で削除済み。設計書のコード例の `BackgroundTasks` は書かない）。
   `from fastapi import APIRouter, Depends, HTTPException, Query, Request, status`
2. import を2行追加（`from db import crud` の付近、既存のスタイルに合わせる）。
   ```python
   from api.limiter import limiter
   from config import LOGIN_RATE_LIMIT
   ```
3. `login` を次の形にする（**本体は変更しない**）。**デコレータの順序は `@router.post` が外側・`@limiter.limit` が内側**。
   ```python
   @router.post("/auth/login")
   @limiter.limit(LOGIN_RATE_LIMIT)
   async def login(request: Request, body: LoginBody):
       """
       ユーザー名・パスワードを検証してJWTトークンを返す。
       GETは不可（URLにパスワードが露出しアクセスログに残るリスクのため）。
       """
       ...（本体は変更しない）
   ```
   - **`request: Request` は第1引数**（slowapi は引数名 `request` で `Request` を受け取る関数にしか適用できない）。
4. 他のエンドポイントにデコレータを付けない（適用対象は **`POST /api/auth/login` のみ**）。

---

## 3. `backend/main.py`・`backend/config.py`・`backend/requirements.txt`

### 3-1. `config.py`

`METRICS_WINDOW_DAYS` の直後に追加する（他の定数は追加しない）。

```python
# レートリミット設定（F-17）
LOGIN_RATE_LIMIT = "5/minute"
```

### 3-2. `requirements.txt`

末尾（`psycopg[binary]` の次の行）に **`slowapi`** を1行追加する。**バージョンは固定しない**（設計§2-7）。

### 3-3. `main.py`

1. import を追加（既存の import 群のスタイルに合わせて、`from api.routes import router as api_router` の付近）。
   ```python
   from slowapi import _rate_limit_exceeded_handler
   from slowapi.errors import RateLimitExceeded

   from api.limiter import limiter
   ```
2. `app = FastAPI(title="NBA News JP")` の直後に追加。**`limiter` は生成せず import したものを使う**。
   ```python
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   ```
3. `uvicorn.run(...)` に2引数を追加（既存の引数は変更しない）。
   ```python
   proxy_headers=True,
   forwarded_allow_ips="*",
   ```
4. `_scheduler_enabled()`・`startup_event()`・`shutdown_event()` は変更しない（7-A-10c の成果）。

---

## 4. フロントエンド（429 の UI・詳細設計書 §4-2-1）

**現行は 429 も 401 と同じ文言になる**（`useAuth.js` L15 が一括で例外、`LoginForm.jsx` L13 が固定文言）。

### 4-1. `frontend/src/hooks/useAuth.js` L15

```javascript
// 変更前
if (!res.ok) throw new Error('ログインに失敗しました');
// 変更後
if (!res.ok) {
  const err = new Error('ログインに失敗しました');
  err.status = res.status;
  throw err;
}
```

### 4-2. `frontend/src/components/LoginForm.jsx` L11-15

```javascript
// 変更前
try { await onLogin(username, password); }
catch { setError('ユーザー名またはパスワードが正しくありません'); }
// 変更後
try { await onLogin(username, password); }
catch (e) {
  setError(
    e.status === 429
      ? 'ログインの試行が多すぎます。1分ほど待ってから再試行してください。'
      : 'ユーザー名またはパスワードが正しくありません'
  );
}
```

> 実際の字下げ・改行は既存コードのスタイルに合わせる。**文言は設計書どおり一字一句変えない**（T-P3-14 が後でこの文字列を検証する）。

---

## 5. `backend/tests/conftest.py` の改修

テスト設計書 §2-0 #1・#3・#4 と §1-6-2 対処1・2 を実施する。**あわせて、7-A-10 で判明した `DATABASE_URL` の穴（テスト設計書 v0.7 に引き継ぎ済み）も塞ぐ。**

### 5-1. `.env` 読み込みの削除（対処1）

**L6-11（`from dotenv import load_dotenv` と `load_dotenv(...)` の呼び出し）を削除する。**（`app/.env` は存在せず no-op だが、作られた瞬間に実値でテストが動き出す。）

### 5-2. ダミー値を無条件代入にする（対処2）＋ `DATABASE_URL`

`os.environ.setdefault(...)` の5行を **`os.environ["..."] = "..."`（無条件代入）** に変え、`DATABASE_URL` を1行追加する。値は現行のダミーのまま。

```python
os.environ["ANTHROPIC_API_KEY"]   = "sk-ant-test-dummy-key"
os.environ["BALLDONTLIE_API_KEY"] = "test-dummy-key"
os.environ["SECRET_KEY"]          = "test-secret-key-for-testing-purposes-only-32chars"
os.environ["USERNAME"]            = "testuser"
os.environ["USER_PASSWORD"]       = "testpass123"
os.environ["DATABASE_URL"]        = "sqlite:///test_dummy.db"   # 本番URLが混入しても collection が壊れないようにする（実際のテストは conftest 自前のエンジンを使うため値は使われない）
```

### 5-3. `api_client`・`raw_api_client` に limiter を設定（§2-0 #1）

**両方のフィクスチャ**で、`app.include_router(...)` の前後どちらでもよいので追加する。

```python
from api.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### 5-4. 各テストの前にカウンタを初期化（§2-0 #3）

```python
@pytest.fixture(autouse=True)
def reset_rate_limit():
    from api.limiter import limiter
    limiter.reset()
    yield
```

### 5-5. 変更しないもの

`patch_db_session`・`reset_db` および既存のダミー値（値そのもの）。`cors_client` は 7-A-5。

---

## 6. `backend/tests/test_rate_limit.py`（新規・T-P3-01）

テスト設計書 T-P3-01 の **TC-01-1〜6** を実装する。ユーザーの作り方・認証情報の渡し方は **`tests/test_auth.py`（L19・L36・L46・L60 付近）の既存パターンに揃える**。

| ケース | 使うクライアント | 操作 | 期待 |
|---|---|---|---|
| TC-01-1 | `raw_api_client` | 正しい認証情報で1回ログイン | **200**・`access_token` あり |
| TC-01-2 | 同上 | 誤った認証情報で**5回**連続 | **5回とも 401**（429 にならない） |
| TC-01-3 | 同上 | 誤った認証情報で**6回**連続 | 1〜5回目 401・**6回目 429** |
| TC-01-4 | 同上 | TC-01-3 の直後に**正しい**認証情報で1回 | **429**（成否ではなくリクエスト数で制限される） |
| TC-01-5 | `api_client`（認証オーバーライドあり） | `GET /api/news` を6回連続 | **いずれも 429 にならない** |
| TC-01-6 | `raw_api_client` | 6回目の 429 の前後で `users` を比較（件数・`hashed_password`） | **変化なし**（ロックアウトしない） |

- 制限値は**テストに `"5/minute"` を直書きせず `config.LOGIN_RATE_LIMIT` から導く**（回数の根拠を本番の定数に結びつける。例：`int(LOGIN_RATE_LIMIT.split("/")[0])`）。
- `forwarded_allow_ips` は単体テストで検証できない（`TestClient` はプロキシを経由しない）。**本番確認（§9）で行う。**

---

## 7. 検証（Claude Code）

| # | 確認 | 期待 |
|---|---|---|
| 1 | `pip install -r requirements.txt`（`slowapi` を入れる）の後、`Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue` → `pytest` | **全件 passed**（現在 98 ＋ 新規 TC-01-1〜6 ＝ **104 passed** 想定。件数を報告） |
| 2 | **hermetic 確認**：`$env:DATABASE_URL="postgresql+psycopg://dummy:dummy@localhost/dummy"`・`$env:SECRET_KEY="shell-export-value"` を設定して `pytest` → 終わったら `Remove-Item Env:\DATABASE_URL, Env:\SECRET_KEY` | **同じく全件 passed**（5-1・5-2 の効果の実証。ダミー値はいずれも実在しない値） |
| 3 | `grep -rn "setdefault\|load_dotenv" backend/tests/conftest.py` | **0 件** |
| 4 | `python -c "from api.routes import router; print(sorted(r.path for r in router.routes))"` | `/auth/login` を含み、他のパスが増減していない |
| 5 | `grep -rn "limiter" backend --include=*.py`（`tests/` を除く） | `api/limiter.py`（生成）・`routes.py`（import・デコレータ）・`main.py`（import・`app.state`）のみ。**`Limiter(` が1箇所だけ** |
| 6 | `npm run lint`（`frontend/`） | **errors が増えていない**（既存4件＝`useNews.js` 由来のみ。本変更のファイルに新規エラーなし） |
| 7 | `npm run build`（`frontend/`） | 成功 |
| 8 | `git diff --stat` | §0-1 の 8 ファイル（＋新規2）のみ。**`.env`・`render.yaml`・`batch.yml` を含まない** |

---

## 8. 報告

1. pytest の件数（#1・#2 の両方）。
2. 検証 #3〜#8 の結果。
3. 変更後の `routes.py` の import 部と `login` 関数のシグネチャ、`main.py` の `app.state.limiter` 付近と `uvicorn.run` 全文、`conftest.py` の冒頭（L1〜30 付近）。
4. 設計書との差異（`BackgroundTasks` の扱い、`config.ENABLE_SCHEDULER` を採らないこと等）。
5. 失敗・不安定なテストがあれば再現条件。**既知：`test_crud.py::test_t10_delete_old_articles` は秒境界で不安定**（本変更とは無関係・触らない）。
6. commit は Takumi様が確認してから。

---

## 9. 本番確認（Takumi様・push 後・PowerShell）

**`requirements.txt` に `slowapi` が増えるため、Render のビルドでインストールされる。** デプロイが失敗しても Live は直前の成功版のまま残る（F7 で確認済み）。

### 9-1. 基本動作（偽装なし）

```powershell
$u = "https://nba-news-backend-ppsd.onrender.com/api/auth/login"
$body = '{"username":"ratelimit-test","password":"wrong"}'
function Try-Login($xff) {
  $h = @{}; if ($xff) { $h["X-Forwarded-For"] = $xff }
  try { Invoke-WebRequest -Method Post -Uri $u -Body $body -ContentType "application/json" -Headers $h -UseBasicParsing | Out-Null; 200 }
  catch { [int]$_.Exception.Response.StatusCode }
}
1..7 | ForEach-Object { Try-Login $null }
```

**期待：`401` が5回 → `429` が2回**（最初の1回はスピンダウン復帰で1分かかることがある）。

### 9-2. 🔴 X-Forwarded-For の偽装でバイパスできないか

**61秒待ってから**、リクエストごとに違う偽装 IP を付ける。

```powershell
Start-Sleep 61
1..7 | ForEach-Object { Try-Login "203.0.113.$_" }
```

| 結果 | 判定 |
|---|---|
| **どこかで `429` が出る** | ✅ 偽装は効かない（Render が `X-Forwarded-For` を上書きしている／偽装値が使われていない）。設計どおりで完了 |
| **7回とも `401`（429 が出ない）** | 🔴**バイパスできる**。`forwarded_allow_ips="*"` では uvicorn が **X-Forwarded-For の先頭（クライアントが付けた値）**を採るため、**リクエストごとに偽装 IP を変えるとレート制限が無効になる**。**直ちに報告すること**（追加の対処＝キー関数の変更を別途設計する） |

> **背景**: 設計§2-4-2 は「Render 以外から直接ポートに到達できない」ことを前提に `forwarded_allow_ips="*"` としたが、**Render が受信した `X-Forwarded-For` を上書きするか追記するかは公式に確認できていない**（コミュニティでは「追記のみ」との報告と、「先頭がクライアント IP」との報告が食い違う）。**実測で確かめる**。テスト用の偽ユーザー名（`ratelimit-test`）への 401 試行のみで、実アカウントは影響を受けない。

### 9-3. 通常動作

ログインが成功すること（`USERNAME`／`USER_PASSWORD`）。**9-1・9-2 の直後は 429 が最大1分続く**ため、1〜2分待ってから行う。ブラウザで**誤った認証情報を6回続けて入力し、6回目に「ログインの試行が多すぎます。1分ほど待ってから再試行してください。」が出る**ことも確認する（UI の 429 表示）。

報告してほしいのは：9-1 の結果（ステータス列）・9-2 の結果（ステータス列）・9-3 の UI 表示の有無。
