# 実装指示 SEC-1：eMudhra 証明書侵害への対応 ＋ 設計書レビュー指摘の反映

作成日：2026-10-27 ／ 主担当：Claude Code（実装・文書修正）→ Takumi様（commit・push・Render 設定・本番確認）

**関連**
- Render アドバイザリ「eMudhra Certificate Compromise」（2026-10-22 公開・`https://render.com/docs/advisory-emudhra`）
- Render からのメール（2026-10-26 受信。eMudhra／Node.js／PHP2Shell の3件）
- python.org 告知「Information for Python users regarding eMudhra / emSign CA certificate security incident」（`https://discuss.python.org/t/.../109576`）
- レビュー結果報告書3件（本指示と同時に提出）
  - `docs/Basic_Design/review_basic_design_p3_v0.9.txt`（🔴0／🟡1／🟢2）
  - `docs/Detail_Design/review_detail_design_p3_v0.5.txt`（🔴0／🟡0／🟢2）
  - `docs/Test_Design/review_test_design_p3_v0.7.txt`（🔴0／🟡1／🟢1）

**前提**：7-A 完了・7-B は Section C クローズ待ち（11月上旬見込み）。**本指示は 7-B に依存せず、いま実施できる**（UI に触らない）。

**位置づけ**：工程外対応。先-1・先-2 と同じく**実施記録を残す**（計画書§5-2「工程外先行対応の実施記録」）。検証は計画書の**「A. コード変更を伴う場合」のルールを準用**する。ベースライン§3の残課題には紐づかないため、ベースラインの更新は不要。

---

## 0. 本指示の構成と優先順位

| 区分 | 内容 | 緊急度 | commit |
|---|---|---|---|
| **A** | eMudhra 証明書侵害への対応（コード・設定・検証） | 🔴 **高**（外部要因・本番が対象） | **A だけで1回** |
| **B** | 設計書レビュー指摘の反映（文書のみ） | 中 | **B で別に1回** |

**A と B は独立している。A を先に完結させてよい。混ぜて1コミットにしないこと**——A は緊急のロールバック対象になりうるため、文書修正を同じコミットに入れると revert の範囲が広がる。

> **番号「SEC-1」は仮**である。計画書の 先-N 体系に合わせて **先-3** とするか、`7-A-14` のようにサブ手順として扱うかは Takumi様の判断に委ねる。ファイル名の変更が必要なら指示されたい。

---

## 1. 背景（調査結果・2026-10-27）

### 1-1. メールの3カテゴリと本プロジェクトの該当範囲

| カテゴリ | 該当 | 根拠 |
|---|---|---|
| **PHP アプリ** | ❌ **無関係** | `*.php`・`composer.json` とも **0件**。Docker も未使用。PHP2Shell（CVE-2026-109618／109619・CVSS 9.2）は**PHP コアエンジンの脆弱性**で共有Cライブラリではないため、Python／Node に波及しない |
| **Node.js アプリ** | ⚠️ **フロントのビルドのみ** | バックエンドは Python。**本番に Node ランタイムは存在しない**（フロントは Static Site＝ビルド済みの静的ファイル）。Vite ビルドが Node を使うため、Render アドバイザリの「Static sites require updating only if your site's build process uses Node.js」に該当 |
| **HTTPS を送るアプリ** | ✅ **該当（本題）** | 下表のとおり外向き HTTPS が5経路ある。証明書の明示指定（`verify=`・`SSL_CERT_FILE` 等）は**コード中に1件も無く**、`requests`／`httpx` の既定＝**certifi**（システムストアではない） |

**外向き HTTPS の経路（実測）**

| # | 宛先 | 呼び出し元 | 証明書ストア |
|---|---|---|---|
| 1 | Claude API | `processor/claude_client.py`（`anthropic` → `httpx`） | **certifi** |
| 2 | `api.balldontlie.io` | `fetcher/score.py` L34・L79（`requests`） | **certifi** |
| 3 | RSS 3ソース（`hoopsrumors.com`／`hoopswire.com`／`thecoldwire.com`） | `fetcher/rss.py` L17（`requests`） | **certifi** |
| 4 | healthchecks.io | `run_batch_once.py` L45（`requests`） | **certifi** |
| 5 | Neon（PostgreSQL） | `db/models.py` L83（`psycopg` → libpq／OpenSSL） | **システムCAストア** |

### 1-2. なぜ Python でも対応が必要か（4層ある）

Render は「ネイティブランタイムは次のビルドでシステムCAストアが更新される」としているが、**Python の `requests`／`httpx` はシステムストアを使わない**。層ごとに別の対処が要る。

| 層 | 対象 | 対処 | 本指示 |
|---|---|---|---|
| ① **certifi**（アプリの HTTPS 送信） | 経路1〜4 | `certifi>=2026.10.19` に上げる。侵害された中間CAの発行元 **emSign root を削除**した版 | **A-1** |
| ② **システムCAストア** | 経路5（Neon） | Render の**再ビルドで自動更新**される | **A-4** |
| ③ **pip の vendored certifi** | 依存の取得そのもの | pip < 26.2.2 は**vendored certifi をシステムストアに加えて常に信頼し、無効化する手段がない**（python.org・Christian Heimes）。バッチは4時間ごとに `pip install` を HTTPS で実行するため、ここが実質の MITM 面 | **A-2** |
| ④ **Python 本体（ssl モジュール）** | 全経路の多層防御 | **3.11.18 以降**は、侵害された中間CAを **SPKI ハッシュで拒否**する。certifi やシステムストアが古くても効く。**Sectigo AAA でクロス署名された経路（root 削除だけでは防げない）にはこれが必要** | **A-3** |

> **①だけでは足りない理由**：侵害されたのは**中間**CAであり、同じ鍵が **Sectigo の AAA Certificate Services** 配下にクロス署名された版も存在する。emSign root を消しても AAA 経由の経路は残るため、④の SPKI 拒否が要る。Render アドバイザリの検証用エンドポイントが **2つ**あるのはこの区別のためである（A-5）。

### 1-3. 対応しないもの（根拠を記録する）

| 項目 | 判定 | 根拠 |
|---|---|---|
| PHP の更新 | **不要** | PHP を使っていない（§1-1） |
| バックエンドの Node.js 版の設定 | **不要** | Python サービスのビルド・実行に Node を使わない。Render も「does not use Node.js at all during its builds or at runtime」なら skip してよいとしている |
| `npm audit` 14件（high 11・`vite` 8.0.0–8.0.15 を含む。handover_7-B §2 #6） | **本指示の範囲外** | `package-lock.json` があるため **`npm ci` は固定され、再デプロイしても依存は上がらない**。上がるのは Node 本体のみ。audit は 7-B 開始時の予定どおり別途扱う |

---

## 2. 変更するファイル

| 区分 | ファイル | 種別 | 担当 |
|---|---|---|---|
| **A-1** | `app/backend/requirements.txt` | 変更（2行追加） | Claude Code |
| **A-2** | `.github/workflows/batch.yml` | 変更（ステップ追加） | Claude Code |
| **A-3** | `render.yaml`（リポジトリルート） | 変更（`PYTHON_VERSION` 追加） | Claude Code（**§5 の手順を厳守**） |
| **A-5** | `app/backend/main.py` | **一時的な変更**（検証後に削除） | Claude Code |
| **B** | 基本設計書・詳細設計書・テスト設計書の次版 | 新規作成（差分改訂） | Claude Code |

**他は変更しない**（`api/limiter.py`・`config.py`・`routes.py`・`scheduler.py`・`conftest.py`・既存テスト・フロントのソース・`package.json`・`package-lock.json`）。

**🔴 `.env` を読まない**（`cat`／`head`／`grep`／エディタでの閲覧を含む）。値の確認が必要なら Takumi様に依頼する。環境変数は**キー名のみ**扱う。

---

## 3. 【A-1】`app/backend/requirements.txt`

### 3-1. 変更前に記録する（必須）

**`requirements.txt` は `bcrypt<4.0.0` 以外すべて版無指定である。** したがって再ビルドすると fastapi・sqlalchemy・anthropic・psycopg なども**同時に最新へ上がる**。「証明書だけ直す」作業ではない。

変更前に、現在の解決結果を記録する。

```powershell
cd app\backend
Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue
python -m pip freeze > ..\..\pip_freeze_before_SEC-1.txt
```

この**ファイルは commit しない**（報告に貼る）。`.gitignore` に入っていない場合は作業後に削除する。

### 3-2. 追記する2行

末尾に次を追記する。既存行は**並び替えない・消さない**。

```text
certifi>=2026.10.19
sqlalchemy>=2.0
```

| 行 | 根拠 |
|---|---|
| `certifi>=2026.10.19` | Render アドバイザリの Python 向け指示そのもの（「confirm that your dependency or lockfile resolves `certifi` to `2026.10.19` or later」）。現在 certifi は `requests`／`httpx` の transitive 依存で版が固定されていない |
| `sqlalchemy>=2.0` | **詳細設計書§6 #15 の消化**（「次の `requirements.txt` 変更時に判断する」＝いまがその機会）。§2-7 は「2.0系から下げない」と設計しているが機械的に担保されていなかった。**下限のみなので現在の解決結果は変わらない** |

> **`sqlalchemy>=2.0` を外したい場合は外してよい。** A の緊急度は `certifi` にあり、`sqlalchemy` は設計の明文化にすぎない。外す場合は §6 #15 を ⬜ のまま残し、報告にその旨を書く。

### 3-3. 変更後に記録する

```powershell
python -m pip install -r requirements.txt --upgrade
python -m pip freeze > ..\..\pip_freeze_after_SEC-1.txt
python -c "import certifi; print('certifi', certifi.__version__, certifi.where())"
```

**before／after の差分を全件報告する。** certifi 以外に上がったパッケージがあれば、それがテストに影響しないことを §7 で確認する。

---

## 4. 【A-2】`.github/workflows/batch.yml`

`actions/setup-python` の後、`pip install -r` の**前**に2ステップ挿入する。既存のステップ・`cron` 式・`env` の4シークレットは**変更しない**。

```yaml
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: pip

      # SEC-1：pip < 26.2.2 は vendored certifi をシステムストアに加えて常に信頼し、
      # 無効化する手段がない（python.org の告知）。依存の取得経路を先に塞ぐ。
      - name: Upgrade pip
        run: python -m pip install --upgrade "pip>=26.2.2"

      # SEC-1：障害調査用に版を残す（恒久）。certifi は 2026.10.19 以降であること。
      - name: Show versions
        run: |
          python -VV
          python -m pip --version
          python -c "import certifi; print('certifi', certifi.__version__)"

      - run: pip install -r app/backend/requirements.txt
```

**注意点**

| # | 内容 |
|---|---|
| 1 | `cache: pip` のキャッシュキーには **`requirements.txt` のハッシュ**が含まれる。A-1 でファイルを変えるため**キャッシュは必ず作り直される**。`cache: pip` を外す必要はない |
| 2 | `Upgrade pip` 自体は**更新前の pip で HTTPS 通信する**。より厳密にやるなら python.org が示す「直URL＋sha256」方式を使う（下記）。ただし GitHub の runner イメージは GitHub 側も更新しているため、まずは `Show versions` の出力で**現在の pip が既に 26.2.2 以上かを確認**し、足りていれば `Upgrade pip` は no-op として残す |
| 3 | 厳密版（任意）：`python -m pip install "pip @ https://files.pythonhosted.org/packages/.../pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70"`。**URL とハッシュは python.org の告知から転記し、勝手に作らない**。版が上がると陳腐化するため、恒久運用には向かない |
| 4 | `python-version: '3.11'` は runner のツールキャッシュにある**最新の 3.11.x** に解決される。`Show versions` の `python -VV` で **3.11.18 以降**であることを確認する。満たない場合は `'3.11.18'` に固定して報告する |

---

## 5. 【A-3】`render.yaml` に `PYTHON_VERSION` を追加

### 5-1. 🔴 先に現状を読んで報告する（編集しない）

`render.yaml` はリポジトリルートにあり、**Blueprint として連携されている＝正（source of truth）**である。CLAUDE.md の警告：

> 🔴 **Blueprint sync はダッシュボードの値を `render.yaml` の内容で上書きする**（プレースホルダが残ると正しい値が壊れる／`autoDeploy` 未指定は既定の On に戻りうる）。編集は最小回数にまとめる

したがって **`PYTHON_VERSION` をダッシュボードに入れると、次の sync で消える可能性がある。`render.yaml` に書くのが正しい。**

**手順**

1. `render.yaml` の**現在の内容を全文読み、そのまま報告する**（Claude Code）。
2. Takumi様が内容を確認し、編集の可否を指示する。
3. 指示を受けてから編集する。**この順序を飛ばさないこと。**

### 5-2. 編集内容（指示を受けてから）

バックエンド（Web Service）の `envVars` に1件追加する。

```yaml
      - key: PYTHON_VERSION
        value: 3.11.18
```

**守ること**

| # | 内容 |
|---|---|
| 1 | **既存のキーを1つも消さない・値を変えない。** とくにシークレット6件の `sync: false`（`ANTHROPIC_API_KEY`・`BALLDONTLIE_API_KEY`・`SECRET_KEY`・`USERNAME`・`USER_PASSWORD`・`DATABASE_URL`）は**絶対に値を書かない** |
| 2 | **`autoDeploy` の記述を変えない。** 未指定だった場合も**勝手に追記しない**（既定の On に戻る挙動が CLAUDE.md で警告されている。追記の可否は Takumi様の判断） |
| 3 | `healthCheckPath: /healthz` を変えない |
| 4 | Static Site 側には `NODE_VERSION` を**追記しない**（理由は §5-3） |
| 5 | 編集は**この1回にまとめる**（Blueprint sync の回数を増やさない） |

### 5-3. Static Site の Node.js について（追記しない理由）

`frontend/package.json` の `engines.node` は **`">=22.0.0"`＝上限なしの範囲**である。Render のドキュメントは明記している：

> An unbounded range (such as `>=20`) always resolves to the **`latest` release** of Node.js

つまり**再デプロイすれば自動的に patched 版（22.23.4／24.22.1／26.12.1 以降）になる**。いま `NODE_VERSION` を固定すると、かえって版を誤って固定するリスクがある。

ただし Render は「Always include an upper bound」と推奨しており、**上限なしは別途の課題**である。**本指示では触らず、7-B 開始時（handover §2 #6 の `npm audit` 精査と同時）に上限を決める**ことを引き継ぎに入れる。

---

## 6. 【A-4／A-5】証明書拒否の検証

### 6-1. 検証に使うエンドポイント（Render アドバイザリ §4）

| URL | 何を試すか |
|---|---|
| `https://dv-g3b-emudhra.we-have-a-problem.com/` | 侵害された中間CA（emSign root 経由） |
| `https://dv-g3b-aaa-emudhra.we-have-a-problem.com/` | 同じ鍵の **Sectigo AAA クロス署名**版（root 削除だけでは防げない経路） |

**両方とも証明書検証エラーで失敗しなければならない。** どちらかが**成功したら（ステータスコードが 200 以外でも）未対応**である。

> **🔴 `curl` で代替しない。** Render は「サービスのシェルからの `curl` は本番と別のCAストアを使う可能性がある」と明記している。**稼働中のサービスの HTTP クライアント（＝`requests`）から**送る必要がある。

### 6-2. 【A-4】ローカルでの先行確認（Claude Code）

A-1 の `pip install` 後、ローカルで実行して**両方が失敗すること**を確認する。

```powershell
cd app\backend
python -c @"
import requests
for u in ('https://dv-g3b-emudhra.we-have-a-problem.com/',
          'https://dv-g3b-aaa-emudhra.we-have-a-problem.com/'):
    try:
        r = requests.get(u, timeout=5)
        print('NG  reachable', r.status_code, u)
    except requests.exceptions.SSLError as e:
        print('OK  rejected', u)
    except Exception as e:
        print('??  other', type(e).__name__, u)
"@
```

**期待：2行とも `OK  rejected`。** `NG  reachable` が出たら certifi の版が足りていない（報告して止まる）。`??  other` は通信到達性の問題の可能性があるため、例外名を報告する。

> これは**ローカルの certifi** を検証している。本番（Render）の certifi は別であり、A-5 で確認する。

### 6-3. 【A-5】本番（Render Web Service）での確認

無料プランでは **Render Shell が使えない**（handover §2 #5）。本番のアプリ自身に実行させる必要がある。

**方式：起動時に1回だけ実行し、結果をログに出す（推奨）**

外部に何も晒さないため、一時的な診断エンドポイントより安全である。`main.py` の `startup_event()` の**末尾**に次を追加する。

```python
    # TEMP（SEC-1）：eMudhra 証明書拒否の確認。確認後に削除する。
    import requests as _rq
    for _u in ("https://dv-g3b-emudhra.we-have-a-problem.com/",
               "https://dv-g3b-aaa-emudhra.we-have-a-problem.com/"):
        try:
            _r = _rq.get(_u, timeout=5)
            logger.error("SEC-1 NG reachable %s %s", _r.status_code, _u)
        except _rq.exceptions.SSLError:
            logger.info("SEC-1 OK rejected %s", _u)
        except Exception as _e:
            logger.warning("SEC-1 ?? %s %s", type(_e).__name__, _u)
```

**守ること**

| # | 内容 |
|---|---|
| 1 | **URL はハードコードする。** クエリ・環境変数から受け取らない（任意の URL を叩かせない） |
| 2 | `timeout=5` を必ず付ける。**startup を止めない**（スピンダウン復帰が約1分であり、ここで待たせない） |
| 3 | `try/except` で囲み、**例外を外に投げない**。`startup_event()` が失敗するとサービスが起動しない |
| 4 | コメントに **`TEMP（SEC-1）`** を入れる。削除時の `grep` 目印にする（7-A-4b の `TEMP（7-A-4b）` と同じ運用） |
| 5 | `_scheduler_enabled()` の分岐の**外**（無条件に実行される位置）に置く。本番は `ENABLE_SCHEDULER=false` のため、分岐の中に入れると実行されない |

**代替案（Takumi様が起動時実行を避けたい場合）**：JWT 必須の一時エンドポイント（`Depends(get_current_user)`）を立て、確認後に削除する。7-A-4b の `/_diag/client-headers` に前例がある。ただし**認証なしでは立てない**。

### 6-4. 【A-5 後片付け】削除

確認が取れたら**同じコミットサイクル内で削除する**。

```powershell
# リポジトリルートで
grep -rn "TEMP（SEC-1）\|we-have-a-problem" app\backend --include=*.py
```

**期待：0件**（削除後）。削除前は `main.py` の1箇所のみ。

---

## 7. 【A】検証（Claude Code・ローカル）

| # | 確認 | 期待 |
|---|---|---|
| 1 | `Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue` の後に `pytest` | **全件 passed**。**件数を報告**（2026-10-18 時点で 138 passed。増減があれば原因を説明）。`test_crud.py::test_t10_delete_old_articles` は秒境界で不安定（既知・handover §2 #11） |
| 2 | `python -c "import certifi; print(certifi.__version__)"` | **2026.10.19 以降** |
| 3 | §6-2 の2URL チェック | **2行とも `OK  rejected`** |
| 4 | `pip freeze` の before／after 差分 | **全件報告**。certifi 以外の上昇が #1 に影響していないこと |
| 5 | `grep -rn "verify=False\|SSL_CERT_FILE\|REQUESTS_CA_BUNDLE\|CURL_CA_BUNDLE" app/backend --include=*.py` | **0件**（証明書検証を回避している箇所が無いこと） |
| 6 | `git diff --stat` | **§2 の A 区分のファイルのみ**（`requirements.txt`・`batch.yml`・`render.yaml`・`main.py`）。`pip_freeze_*.txt` が含まれていないこと |
| 7 | **ロールバック手段の事前確認**（計画書の検証ルール A） | 直前コミットの SHA を記録し、`git revert` で戻せることを確認・報告 |

---

## 8. 【B】設計書レビュー指摘の反映

**A と別コミットにする。** 版番号は Takumi様の指示に従う（基本設計書 v0.9 の次。計画書は v0.9 → v1.0 の前例あり）。本指示では「次版」と記す。

### 8-1. 基本設計書（次版）

| # | 指摘 | 節 | 作業 |
|---|---|---|---|
| **B-1** | 🟡 **BD9-01** | §8 | **引き継ぎ13件を全件棚卸しし状態欄を更新する。** v0.9 は3件（#4・#11・#13）しか更新せず、**10件が実態と乖離**している。とくに **#8（先-1・期限つき・7-A-1 で 2026-09-19 に完了）が ⬜**、**#6（要望1の採否・2026-09-08 に採用確定）が ⬜**。#8 は §8 の注記が名指しで挙げている期限つき項目であり、**詳細設計書§6 #10 は同じ作業を「✅ 7-A-1（2026-09-19・期限内）」と記録している**（上流が未実施・下流が完了という逆転）。「**✅設計確定／⬜実装待ち**」の2段表記を推奨（#1・#9・#12 のような「手順4・5 としては消化済みだがコードは未」を正確に表せる） |
| **B-2** | 🟢 **BD9-02** | §1-2 #15 | **変更内容に `get_client_ip` を追記し、対応要件を `F-17` にする。** v0.9 は §4-1 を全面改訂して `api/limiter.py` に**キー関数を置くと決めた**のに、§1-2 #15 は v0.8 のまま「`Limiter` インスタンスの単一の生成箇所（循環 import の回避）」としか書いていない。いまこのファイルの中心は**信頼できる IP の決め方**（約15行）である。対応要件欄も `—` のまま |
| **B-3** | 🟢 **BD9-03** | §7-1 [8] | **1語添える。** `[8] main.py L68-73 uvicorn.run() に forwarded_allow_ips 指定なし ✅一致` は **v0.8 時点で「まだ追加していない」ことの記録**だが、v0.9 が `forwarded_allow_ips` を撤回した結果、**文字列として現行の正しい状態と一致してしまう**。「結論が一致するのは偶然であり、同じ確認ではない」と明記する（履歴宣言は既にあるため、この1行のみ） |

### 8-2. 詳細設計書（次版）

| # | 指摘 | 節 | 作業 |
|---|---|---|---|
| **B-4** | 🟢 **DD5-01** | §6 #16・#17 | **状態欄を ✅ にし、実施日と反映先を添える。** 両方 2026-10-21 に完了している（#16 → 基本設計書 v0.9 の是正対応表 #1〜#4 と1対1／#17 → テスト設計書 v0.7 の TC-01-7・01-8・K-1〜K-6 ほか）。**#17 は引き継ぎ先を「テスト設計書 v0.7」と版番号まで指定しており、その v0.7 が実在するのだから ⬜ は矛盾**。なお **#15 は ⬜ のままで正しい**（`requirements.txt` が版無指定だった）が、**本指示 A-1 で `sqlalchemy>=2.0` を入れるなら ✅ に更新する** |
| **B-5** | 🟢 **DD5-02** | §5-1 の宣言 | 例の書き方を分ける。現在「`main.py` の `uvicorn.run` は**変更なし**」とあるが、**行番号は L68-73 → L83-88 に移動している**（7-A で `/healthz`・`_scheduler_enabled()` が追加されたため）。行番号の陳腐化を説明する文の中の例なので、「この行は信用してよい」と読める。「**内容は不変だが位置が L68-73 → L83-88 に移動**」に改める |
| **B-6** | — | §2-7・§3-3 | **本指示 A の内容を設計に反映する。** §2-7（`requirements.txt` への追加）に **`certifi>=2026.10.19`**（および採用すれば `sqlalchemy>=2.0`）を追記。§3-3 の `batch.yml` に **`Upgrade pip`・`Show versions` の2ステップ**を反映。**A を実装したら設計書がその分だけ古くなる**ため、B と同時に処理する |

### 8-3. テスト設計書（次版）

| # | 指摘 | 節 | 作業 |
|---|---|---|---|
| **B-7** | 🟡 **TD7-01** | §8-2 の2項目 | **F8 を生んだ判断が ✅ のまま残っている。** 本文（T-P3-01）は v0.7 で「二重に誤りだった」と訂正済みだが、自己チェック記録は未訂正。①「設計値が実環境で意図どおり働くか → `forwarded_allow_ips` は **`TestClient` では検証できない**ことを確認し…**ここを単体テストに書くと通っても意味がない**」②「自動化できないものを…**`forwarded_allow_ips`（実環境依存）**…の4件を**明示的に自動テストの対象外**とし」。②は **K-1〜K-6 として自動化した事実と正面から矛盾**する。**検証できない対象を「①外部システムの挙動（Render が何を付けるか）＝手動確認／②自前のロジック（どの位置を信頼するか）＝自動化できる」に分解して書き換える**。対象外は **4件→3件**（`forwarded_allow_ips` を外す）。あわせて **§9 #3**（「別回線からの同時試行が必要」＝F8 を検出できなかった確認方法）に「🔧 v0.7：偽装試験を含める（§9-1 #21）」と1語添える |
| **B-8** | 🟢 **TD7-02** | §1-2-2 | `main.py` を対象に含める理由を更新する。現在「F-21（CORS）と **`forwarded_allow_ips`（F-17の前提）**が `main.py` にある」だが、`forwarded_allow_ips` は**撤回され `main.py` に存在しない**（実物 L83-88）。一方で**新しい対象が2つ増えている**：**`_scheduler_enabled()`（L56-58。T-P3-16 TC-16-1〜6 が検証）**・`/healthz`（L50-51）。いま `main.py` を含める理由は CORS より `_scheduler_enabled()` の方が大きい |

### 8-4. 文書側の検証（Claude Code）

| # | 確認 | 期待 |
|---|---|---|
| 1 | `grep -rn "forwarded_allow_ips" docs/Test_Design/<新版>` | **残るのは📖履歴的記述のみ**（§8-2 の現行主張としては0件） |
| 2 | 各文書の件数記述 | §8（13件）・§6（17件）・§0-2 等、**行数と記述が一致**すること |
| 3 | 本文から `§6 #N`・`§8 #N` への番号参照 | **全件突合してずれ0件**（詳細設計書§5-1 A区分の既存項目を実行する） |
| 4 | 変更履歴 | 3文書とも**本指示由来であること**（レビュー由来＝B／製造由来＝A-B6）を区別して記載 |

---

## 9. 報告（Claude Code）

**A と B で分けて報告する。**

**A の報告に含めるもの**
1. `pip freeze` の before／after **全差分**
2. `pytest` の件数（想定 138。増減があれば原因）
3. `certifi` の版・`certifi.where()`
4. §6-2 の2URL チェックの出力（2行）
5. `render.yaml` の**変更前の全文**（§5-1。編集前に提出）と、変更後の差分
6. `batch.yml` の差分と、`Show versions` が出力する想定値
7. §7 の #5・#6・#7（ロールバック手段を含む）
8. 設計書との差異（**A-2 の2ステップは詳細設計書§3-3 に無い**＝B-6 で反映する旨）

**B の報告に含めるもの**
1. 3文書の差分（節単位）
2. §8-4 の検証結果
3. B-1 の棚卸し結果（13件それぞれの新しい状態と根拠）

**commit は Takumi様が確認してから。**

---

## 10. 本番確認（Takumi様・push 後）

### 10-1. Render の操作

| # | 操作 | 対象 |
|---|---|---|
| 1 | **Manual Deploy > Clear build cache & deploy** | **Web Service**（Python）。python.org が「rebuild with layer caching disabled」としているため、通常の「Deploy latest commit」ではなく**キャッシュを消す**。これでシステムCAストア（経路5＝Neon）と certifi の両方が更新される |
| 2 | **Manual Deploy > Deploy latest commit** | **Static Site**（フロント）。Node が patched 版（latest）に解決される |
| 3 | デプロイログの確認 | **Python の版が 3.11.18 以降**であること（`PYTHON_VERSION` が効いている） |
| 4 | デプロイログで `SEC-1` を検索 | **`SEC-1 OK rejected` が2行**。`SEC-1 NG reachable` が出たら未対応（直ちに報告） |

> **⚠️ `render.yaml` を変更したため Blueprint sync が走る。** sync 後に**シークレット6件の値が保持されていること**と、**`autoDeploy` の設定が意図どおりであること**をダッシュボードで確認する（CLAUDE.md の 🔴 警告）。

### 10-2. GitHub Actions

| # | 操作 | 期待 |
|---|---|---|
| 1 | Actions → Run workflow（`workflow_dispatch`）で1回手動実行 | ジョブ成功 |
| 2 | `Show versions` の出力 | `Python 3.11.18` 以降／`pip 26.2.2` 以降／`certifi 2026.10.19` 以降 |
| 3 | バッチの結果 | 記事取得が成功し、healthchecks.io に ping が届く |

### 10-3. 機能確認（ブラウザ）

| # | 確認 |
|---|---|
| 1 | ログインできる（正しい認証情報） |
| 2 | 記事一覧が表示される |
| 3 | ネタバレ防止トグル・チームフィルタの保存が再読込後も保持される（`PUT /api/settings`＝CORS が壊れていない） |
| 4 | 試合日程タブが表示される |
| 5 | コンソールにエラーが出ていない |

> **3〜5 は「依存が一斉に上がった副作用」の検出が目的である。** 証明書の対応とは別に、fastapi・sqlalchemy・anthropic の上昇で壊れていないかを見る。

### 10-4. 一時コードの削除確認

`SEC-1 OK rejected` を確認したら、**A-5 の一時コードを削除して再 push** し、

```powershell
grep -rn "TEMP（SEC-1）\|we-have-a-problem" app\backend --include=*.py
```

が **0件**になること、デプロイログに `SEC-1` が**出なくなる**ことを確認する。

---

## 11. 完了条件

| # | 条件 |
|---|---|
| 1 | §7 の #1〜#7 がすべて期待どおり |
| 2 | 本番の Web Service・Static Site がともに再デプロイ済み（Web はキャッシュ削除つき） |
| 3 | デプロイログで `SEC-1 OK rejected` が **2行**（2つのエンドポイントとも拒否） |
| 4 | GitHub Actions の `Show versions` が Python 3.11.18＋／pip 26.2.2＋／certifi 2026.10.19＋ |
| 5 | §10-3 の機能確認5件がすべて ✅ |
| 6 | A-5 の一時コードが削除され `grep` が 0件 |
| 7 | 3文書の次版が作成され、§8-4 の検証が通っている |
| 8 | **実施記録**：計画書§5-2「工程外先行対応の実施記録」と `manufacturing_verification_log_p3.md` に SEC-1 を追記（対応内容・検証結果・実施日）。**手順7.5 の指摘対応表にも「対応済み（フェーズ3工程外・実施日）」として引き継ぐ**（計画書の追跡ルール） |
| 9 | handover_7-B §2 に引き継ぎを追加：**`engines.node` の上限設定**（§5-3。`npm audit` 精査と同時） |

---

## 12. ロールバック

| 事象 | 手順 |
|---|---|
| 依存の上昇で本番が壊れた | **Render の Rollbacks で直前の成功デプロイに戻す**（無料プランでも利用可）。そのうえで `requirements.txt` の `certifi>=2026.10.19` だけを残し、他の上昇を抑える手段（版の上限指定）を検討する |
| `render.yaml` の sync でシークレットが壊れた | ダッシュボードで値を再入力（`sync: false` のため値はファイルに無い）。**値は Takumi様のみが扱う** |
| 一時コードで startup が失敗した | A-5 の `try/except` が効いていない。直前コミットへ `git revert` して push |

> **🔴 本番で環境変数を空にする等の異常系を試さないこと**（計画書の検証ルール）。異常系の確認はローカルに限る。

---

## 補足：本指示を分割したい場合

A を**さらに2段に分けること**もできる。

| 段 | 内容 | 利点 |
|---|---|---|
| **A 前半** | A-1（`certifi`）＋A-2（`batch.yml`）＋A-4（ローカル検証） | **`render.yaml` に触らずに**バッチ側を先に塞げる。Blueprint sync のリスクを後回しにできる |
| **A 後半** | A-3（`render.yaml`）＋A-5（本番検証）＋後片付け | Web Service 側。sync の確認を集中して行える |

バッチ（4時間ごとに外部へ HTTPS を送る）の方が露出が多いため、**分けるなら前半を先に**。Takumi様の判断に委ねる。
