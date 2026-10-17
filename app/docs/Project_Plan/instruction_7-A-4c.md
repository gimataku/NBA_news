# 実装指示 7-A-4c：レート制限のキー関数の修正（F8 対処）と診断エンドポイントの削除

作成日：2026-10-17 ／ 主担当：Claude Code（実装）→ Takumi様（commit・push・本番確認）
関連：7-A-4（F-17）本番確認 §9-2 で `X-Forwarded-For` 偽装によるバイパスが成立（F8）→ 7-A-4b の計測で原因と対処を確定
前提：7-A-4・7-A-4b が push 済み（本番に `/_diag/client-headers` が存在する）

## 0. 背景（7-A-4b の計測結果・2026-10-17）

| 計測 | 結果 |
|---|---|
| 偽装なし | `X-Forwarded-For`＝「実IP, プロキシ」。`CF-Connecting-IP`・`True-Client-IP`＝実IP |
| `X-Forwarded-For: 偽装値` を付与 | 「**偽装値**, 実IP, プロキシ」（Render は**上書きせず右に追記**）。アプリが見る IP は**偽装値**（uvicorn が先頭を採る）＝**F8 の原因** |
| `CF-Connecting-IP` を単独で偽装 | **403 で拒否**（アプリに届かない） |
| `True-Client-IP` を単独で偽装 | 通るが**実IPに上書きされる** |
| プロキシ側の IP | リクエストごとに変わる（右端は安定したキーにならない） |

**結論**：`CF-Connecting-IP`（クライアントが設定できない）を第一のキーにする。無ければ **`X-Forwarded-For` の右から2番目**（実IP の位置）。**先頭は使わない**（偽装できる）。

## 1. 変更するファイル

| # | ファイル | 種別 |
|---|---|---|
| 1 | `backend/api/limiter.py` | 変更（キー関数） |
| 2 | `backend/main.py` | 変更（診断エンドポイントの削除・`uvicorn.run` の引数） |
| 3 | `backend/tests/test_rate_limit.py` | 変更（テスト追加） |

**他は変更しない**（`routes.py`・`conftest.py`・`config.py`・フロント・`render.yaml`）。`.env` を読まない。

## 2. `backend/api/limiter.py`

```python
from slowapi import Limiter
from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    """レート制限のキー（クライアント IP）。

    Render は Cloudflare の背後にあり、X-Forwarded-For は「クライアントが付けた値…, 実IP, プロキシ」
    の形になる（Render は上書きせず右に追記する）。先頭は偽装できるため使わない。
    1. CF-Connecting-IP（Cloudflare が設定する。クライアントが付けたものはエッジで拒否される）
    2. X-Forwarded-For の右から2番目（実IP の位置）
    3. request.client.host（ローカル開発・ヘッダが無い場合）
    """
    cf = request.headers.get("cf-connecting-ip")
    if cf and cf.strip():
        return cf.strip()
    xff = request.headers.get("x-forwarded-for")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if len(parts) >= 2:
            return parts[-2]
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=get_client_ip)
```

- `get_remote_address` の import は削除する。**`Limiter(` は引き続き1箇所のみ**。
- 根拠のコメントは上記のまま残す（将来「先頭の方が素直」と戻されないようにするため）。

## 3. `backend/main.py`

1. **`/_diag/client-headers` エンドポイントと、そのためだけに追加した import（`Request`）を削除する。** 削除後 `grep -rn "TEMP（7-A-4b）\|_diag" backend/` が **0 件**になること。
2. `uvicorn.run(...)` から **`proxy_headers=True,` と `forwarded_allow_ips="*",` の2行を削除**する（既定値に戻す）。
   - 理由：キーは `limiter.py` が**ヘッダから直接**取り出すため、uvicorn に `X-Forwarded-For` の先頭を `request.client.host` へ反映させる必要がない。**`forwarded_allow_ips="*"` を残すと、フォールバック（`request.client.host`）が偽装できる値になる**。既定（信頼するのは `127.0.0.1` のみ）なら、フォールバックは Render のプロキシ IP になり、**偽装では分割されない**（安全側）。
   - 設計書（詳細設計書§2-4-2）からの逸脱であり、F8 の対処。**詳細設計書 v0.5 で改訂する**。
3. `app.state.limiter`・`add_exception_handler`・`_scheduler_enabled()` 等は変更しない。

## 4. `backend/tests/test_rate_limit.py`（追加）

既存の TC-01-1〜6 は変更しない。次を追加する（`LIMIT` は既存の `config.LOGIN_RATE_LIMIT` 由来の値を使う）。

### 4-1. キー関数の単体テスト（`get_client_ip`）

`starlette.requests.Request` をスコープから組み立てる（例：`Request({"type": "http", "headers": [(b"x-forwarded-for", b"a, b, c")], "client": ("9.9.9.9", 1234)})`）。

| ケース | ヘッダ | 期待 |
|---|---|---|
| K-1 | `CF-Connecting-IP: 1.1.1.1` のみ | `1.1.1.1` |
| K-2 | `CF-Connecting-IP: 1.1.1.1` と `X-Forwarded-For: 2.2.2.2, 3.3.3.3, 4.4.4.4` | **`1.1.1.1`**（CF が優先） |
| K-3 | `X-Forwarded-For: spoof, 5.5.5.5, 6.6.6.6`（CF なし） | **`5.5.5.5`**（右から2番目・先頭の偽装値は使わない） |
| K-4 | `X-Forwarded-For: 7.7.7.7`（1要素・CF なし） | `request.client.host` |
| K-5 | ヘッダなし | `request.client.host` |
| K-6 | `request.client` が `None`・ヘッダなし | `"unknown"` |

### 4-2. 結合テスト（`raw_api_client`）

| ケース | 操作 | 期待 |
|---|---|---|
| **TC-01-7（F8 の回帰）** | 誤った認証情報で **`LIMIT + 1` 回**、毎回 **`X-Forwarded-For: spoof{i}, 203.0.113.50, 198.51.100.1`**（先頭だけ変える） | `[401] * LIMIT + [429]`（**偽装を変えても同じバケット**） |
| **TC-01-8（IP 単位）** | `CF-Connecting-IP: 203.0.113.1` で `LIMIT + 1` 回（最後は 429）→ 続けて `CF-Connecting-IP: 203.0.113.2` で1回 | 2つ目のクライアントは **401**（429 でない＝別バケット） |

> **TC-01-7 が本変更の核心**。このテストが無いと、キー関数を「先頭」に戻す変更が、次に誰かが「素直に」書き直したときに素通りする。

## 5. 検証（Claude Code）

| # | 確認 | 期待 |
|---|---|---|
| 1 | `Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue` の後に `pytest` | **全件 passed**（104 ＋ K-1〜K-6 の6件 ＋ TC-01-7・TC-01-8 の2件 ＝ **112 passed** 想定。件数を報告） |
| 2 | `grep -rn "TEMP（7-A-4b）\|_diag\|get_remote_address\|forwarded_allow_ips\|proxy_headers" backend/ --include=*.py` | **0 件** |
| 3 | `grep -rn "Limiter(" backend --include=*.py` | **1 件**（`api/limiter.py`） |
| 4 | `git diff --stat` | §1 の3ファイルのみ |

## 6. 報告

pytest の件数／検証 #2〜#4／変更後の `limiter.py` 全文と `main.py` の `uvicorn.run` 全文／設計書との差異（`forwarded_allow_ips` を使わないこと）。commit は Takumi様が確認してから。

---

## 7. 本番確認（Takumi様・push 後・PowerShell）

**ステップ間は61秒以上空ける**（制限の窓が1分のため）。

```powershell
$u = "https://nba-news-backend-ppsd.onrender.com/api/auth/login"
$body = '{"username":"ratelimit-test","password":"wrong"}'
function Try-Login($headers) {
  try { Invoke-WebRequest -Method Post -Uri $u -Body $body -ContentType "application/json" -Headers $headers -UseBasicParsing | Out-Null; 200 }
  catch { [int]$_.Exception.Response.StatusCode }
}
# 9-1：偽装なし（期待：401×5 → 429×2）
1..7 | ForEach-Object { Try-Login @{} }
Start-Sleep 61
# 9-2：X-Forwarded-For の先頭を毎回変えて偽装（🔴 以前は7回とも401。期待：401×5 → 429×2）
1..7 | ForEach-Object { Try-Login @{ "X-Forwarded-For" = "203.0.113.$_" } }
Start-Sleep 61
# 9-3：True-Client-IP を毎回変えて偽装（期待：401×5 → 429×2＝上書きされるので効かない）
1..7 | ForEach-Object { Try-Login @{ "True-Client-IP" = "203.0.113.$_" } }
```

| 結果 | 判定 |
|---|---|
| 3つとも **401×5 → 429×2** | ✅ F8 解消 |
| 9-2 が**今回も 7回とも 401** | 🔴 バイパスが残っている。直ちに報告 |
| 9-1 で 429 が出ない | 🔴 全アクセスが別バケットになっている（キー関数の不具合）。直ちに報告 |

最後に、**ブラウザでログインできること**（正しい認証情報）と、**`/_diag/client-headers` が 404 になっていること**を確認する。

```powershell
try { Invoke-WebRequest -Uri "https://nba-news-backend-ppsd.onrender.com/_diag/client-headers" -UseBasicParsing | Out-Null; "status: 200（診断エンドポイントが残っている）" } catch { "status: " + [int]$_.Exception.Response.StatusCode }
```

期待：`status: 404`。
