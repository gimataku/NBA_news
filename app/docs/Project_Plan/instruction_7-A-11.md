# 実装指示 7-A-11：`/api/fetch` と `test_post_fetch()` の削除

作成日：2026-10-14 ／ 主担当：Claude Code（実装）→ Takumi様（commit・push・本番確認）
設計：詳細設計書 v0.4 §3-5／基本設計書§5-4・§8 #4
前提：✅ 7-A-10 完了（`workflow_dispatch` の動作確認済み＝手動実行の代替手段が存在する）

## 0. 目的と範囲

手動バッチ起動の API（`POST /api/fetch`）を削除する。バッチは GitHub Actions の `workflow_dispatch` で手動実行できる。**削除対象は下記のみ。他は一切変更しない。**

## 1. 現状（2026-10-14 時点・行番号は実測）

| ファイル | 行 | 内容 |
|---|---|---|
| `backend/api/routes.py` | L1 | `from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status` |
| 同 | L8 | `from scheduler import run_batch` |
| 同 | **L105-111** | `@router.post("/fetch")` `async def trigger_fetch(background_tasks, current_user)`（`background_tasks.add_task(run_batch)`・戻り値 `{"message": "バッチ処理を開始しました"}`）。前後に空行2行 |
| `backend/tests/test_routes.py` | L252 | セクションコメント `# ── GET /api/status・POST /api/fetch ──…` |
| 同 | **L263-267** | `def test_post_fetch(api_client, mocker):`（`api.routes.run_batch` をパッチして `POST /api/fetch` → 200） |

> ⚠️ 詳細設計書 v0.4 §3-5 は routes.py の対象を「L104-110」としているが、**7-A-3 の変更（`metrics` の1行追加）で1行ずれて L105-111 が実際の位置**。**設計書の行番号ではなく上の実測に従う**（設計書側は v0.5 で修正する）。

## 2. 変更内容

### 2-1. `backend/api/routes.py`

1. L105-111 の `trigger_fetch()`（デコレータ行から `return` 行まで）を削除する。**前後の空行は、関数間が空行2行になるよう1か所分だけ残す**（`get_status` と `get_settings` の間）。
2. L1 の import から **`BackgroundTasks` だけ**を削除する（他の名前は残す）。
3. L8 の `from scheduler import run_batch` を削除する。
4. **削除前に `grep -n "run_batch\|BackgroundTasks" backend/api/routes.py` を実行し、上記以外の使用箇所が無いことを確認する。** 使用箇所が残る場合は削除せず報告する。

### 2-2. `backend/tests/test_routes.py`

1. **L263-267 `test_post_fetch()`**（前後の空行を整理）を削除する。
2. L252 のセクションコメントを **`# ── GET /api/status ──…`**（`・POST /api/fetch` を除く）に修正する。罫線の長さは既存の他のセクションコメントに揃える。
3. `mocker` を使う他のテストは変更しない。

### 2-3. 変更しないもの（明示）

- `scheduler.py`・`main.py`（`main.py` の `from scheduler import check_and_run_batch, scheduler` は残す。設計§3-5 注記のとおり、**API 起動時に `scheduler` がロードされること自体は変わらない**）
- `run_batch_once.py`・`tests/test_scheduler.py`・`tests/test_integration.py`・`tests/test_claude_client.py`（`run_batch` を直接使うテストはそのまま）
- フロントエンド（`/api/fetch` を呼ぶ箇所は無い。確認済み）
- `render.yaml`・`conftest.py`・`.env`（**読まない**）
- `docs/` 配下（`/api/fetch` を記述した文書の追従は 7-A-13 で行う）

## 3. 検証

| # | 確認 | 期待 |
|---|---|---|
| 1 | `Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue` の後に `pytest` | **98 passed**（99 − `test_post_fetch` 1件）。失敗・エラーなし |
| 2 | `grep -rn "api/fetch\|trigger_fetch\|test_post_fetch" backend/`（`docs/` を除く） | **0 件**（`.pyc` は除く） |
| 3 | `grep -n "run_batch\|BackgroundTasks" backend/api/routes.py` | **0 件** |
| 4 | `python -c "from api.routes import router; print(sorted(r.path for r in router.routes))"` | `/fetch` を含まない |
| 5 | `git diff --stat` | `backend/api/routes.py`・`backend/tests/test_routes.py` の2ファイルのみ |

## 4. 制約（厳守）

- `.env` を読まない。シークレット・接続文字列を出力しない。
- 実バッチ・外部 API・本番へのリクエストを実行しない（本サブ手順は削除のみ）。
- commit は Takumi様が確認してから。

## 5. 報告

1. pytest の件数（98 passed の想定）。
2. 検証 #2〜#5 の結果。
3. 変更後の `routes.py` の L1・L8 付近と、`get_status` 〜 `get_settings` の間の全文。
4. 設計書との差異（L104-110 → L105-111 など）があれば明記。

## 6. push 後の本番確認（Takumi様・PowerShell）

Auto-Deploy が On のため push で再デプロイが走る。デプロイ成功後、**認証なしで** `POST /api/fetch` を叩き、ステータスが変わったことを確認する（削除前は認証なしで **403**（`HTTPBearer`）、削除後は経路自体が無いため **404**）。

```powershell
try { Invoke-WebRequest -Method Post -Uri "https://nba-news-backend-ppsd.onrender.com/api/fetch" -UseBasicParsing | Out-Null; "status: 200（想定外）" } catch { "status: " + [int]$_.Exception.Response.StatusCode }
```

| 結果 | 判定 |
|---|---|
| `status: 404` | ✅削除されている |
| `status: 403` | ❌まだ旧版が動いている（デプロイ未完了か失敗） |
| `status: 200（想定外）` | ❌認証なしでバッチが起動した（あり得ない。直ちに報告） |

あわせて `/healthz` が 200、ログインして一覧が表示されることを確認する。**無料プランのスピンダウン復帰に約1分かかる。**
