# 実装指示 7-A-4b：クライアント IP の取得経路の診断（一時エンドポイント）

作成日：2026-10-15 ／ 主担当：Claude Code（実装）→ Takumi様（commit・push・本番での計測）
関連：7-A-4（F-17）の本番確認 §9-2 で **`X-Forwarded-For` の偽装によるレート制限のバイパスが成立**した（偽装 IP を変えながら7回試して 7回とも 401）

## 0. 目的

レート制限のキー（クライアント IP）を**信頼できる形で取り出す**ために、**Render のプロキシが実際にどんなヘッダを付けて転送してくるか**を実測する。設計書にも公式ドキュメントにも記述がなく（2026-10-15 時点）、推測で直すと再び誤る。

**本サブ手順は診断のための一時エンドポイントを1つ足すだけ**である。計測後に **7-A-4c で削除し、キー関数を修正する**。

## 1. 変更するファイル（1つ）

`backend/main.py` のみ。

### 1-1. 追加するエンドポイント

`/healthz` の定義の直後に追加する（`app` に直接ルートを足す。`api/routes.py` や `router` には足さない）。

```python
# TEMP（7-A-4b）：クライアント IP の取得経路の診断用。計測後に 7-A-4c で削除する。
@app.get("/_diag/client-headers")
def diag_client_headers(request: Request):
    h = request.headers
    return {
        "x_forwarded_for": h.get("x-forwarded-for"),
        "cf_connecting_ip": h.get("cf-connecting-ip"),
        "true_client_ip": h.get("true-client-ip"),
        "x_real_ip": h.get("x-real-ip"),
        "forwarded": h.get("forwarded"),
        "client_host_seen_by_app": request.client.host if request.client else None,
    }
```

- `Request` を `fastapi` から import に追加する（既存の `from fastapi import FastAPI` に足す）。
- **認証は付けない**（Takumi様が curl 相当で叩くため）。**返すのは呼び出し元自身のリクエストヘッダのみ**で、他人の情報や秘密は含まない。
- **コメント `TEMP（7-A-4b）` を必ず残す**（削除漏れを grep で拾えるようにする）。

### 1-2. 変更しないもの

`limiter`・`routes.py`・`conftest.py`・テスト・`render.yaml`・フロント。**このエンドポイントのテストは書かない**（一時的なため）。

## 2. 検証（Claude Code）

| # | 確認 | 期待 |
|---|---|---|
| 1 | `Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue` の後に `pytest` | **104 passed**（件数不変） |
| 2 | `grep -rn "TEMP（7-A-4b）" backend/` | **1 件**（`main.py`） |
| 3 | `git diff --stat` | `backend/main.py` のみ |

## 3. 制約

`.env` を読まない。本番へのリクエストを実行しない。commit は Takumi様が確認してから。

## 4. 報告

pytest の件数・検証 #2〜#3・追加した `main.py` の該当箇所（import 行とエンドポイント全文）。

---

## 5. 計測（Takumi様・push 後・PowerShell）

> **扱い**: 結果には**ご自身のグローバル IP が含まれる**。報告するときは、**ご自身の IP を `ME` に置き換える**こと（それ以外の IP——Render／Cloudflare 側のもの——はそのままで構わない）。

```powershell
$u = "https://nba-news-backend-ppsd.onrender.com/_diag/client-headers"
# A：偽装なし
Invoke-RestMethod -Uri $u | ConvertTo-Json
# B：X-Forwarded-For を偽装
Invoke-RestMethod -Uri $u -Headers @{ "X-Forwarded-For" = "203.0.113.9" } | ConvertTo-Json
# C：Cloudflare 系ヘッダを偽装
Invoke-RestMethod -Uri $u -Headers @{ "CF-Connecting-IP" = "203.0.113.9"; "True-Client-IP" = "203.0.113.9" } | ConvertTo-Json
```

（最初の1回はスピンダウン復帰で1分かかることがある。）

### 当方が見るポイント

| 観点 | 何が分かるか |
|---|---|
| A の `x_forwarded_for` の**要素数**と並び | プロキシが何段あり、**どの位置にクライアントの実 IP が入るか**（右から数えて何番目か） |
| B の `x_forwarded_for` | 偽装値が**そのまま残り、実 IP が右に追記される**のか（＝先頭は信頼できない）／**上書きされる**のか |
| A の `cf_connecting_ip`・`true_client_ip` が出ているか | **Cloudflare 系ヘッダが実在するか**（実在すれば、プロキシ側が設定する信頼できる値の候補） |
| C の `cf_connecting_ip`・`true_client_ip` | 偽装値が**そのまま通る**（＝クライアントが書き換えられる＝使えない）か、**実 IP に上書きされる**（＝使える）か |
| `client_host_seen_by_app` | 現行設定（`forwarded_allow_ips="*"`）でアプリが見ている IP（偽装できる値か） |

## 6. 結果の読み方（当方が 7-A-4c の設計に使う）

| 結果 | 7-A-4c の方針 |
|---|---|
| `cf_connecting_ip` が出ていて、C で**上書きされる** | **`CF-Connecting-IP` をキーにする**（プロキシ側が設定する値） |
| Cloudflare 系は無い／偽装が通る。B で**実 IP が `x_forwarded_for` の右側に追記**されている | **右から N 番目**（N は A の要素数から確定）をキーにする（`TRUSTED_PROXY_HOPS` として定数化） |
| 実 IP がどこにも現れない（偽装値しか見えない） | **IP 単位の制限は成立しない**。**全アクセス共通の1バケット**（キーを固定値にする）に切り替える。単一利用者の個人サイトでは許容するが、**攻撃者の連打で本人のログインも 429 になる**トレードオフを明記する |
