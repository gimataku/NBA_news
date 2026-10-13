# 実装指示 7-A-10c：`main.py` の `ENABLE_SCHEDULER` 分岐（3箇所）

作成日：2026-10-14 ／ 位置づけ：7-A-10 第3区（後戻り限界点）の**前**に実施・push する
根拠：基本設計書 v0.8 §5-3（v0.7 で shutdown 追加）／テスト設計書 v0.6 §6-2（T-P3-16）

## 0. なぜ限界点の前か

`ENABLE_SCHEDULER=false` を 7B で Render に入れても、`main.py` が未実装だと**スケジューラが起動して Neon に書き込む**（GitHub Actions との二重実行）。コードを先に載せ、既定値 `true` により**現行動作を変えない**状態で push しておけば、限界点以降は設定の切替だけになる。

Auto-Deploy は Off なので、push しても本番バックエンドは再デプロイされない（5A で確認済み）。**push 後も Manual Deploy は押さないこと**（`DATABASE_URL` がまだスキームなしのため新コードは起動に失敗する）。

## 1. 変更対象

`backend/main.py` のみ（＋テスト1ファイル追加）。他のファイル・`render.yaml` は変更しない。

## 2. 仕様

| 項目 | 内容 |
|---|---|
| 環境変数 | `ENABLE_SCHEDULER` |
| 判定 | `os.getenv("ENABLE_SCHEDULER", "true").lower() != "false"` が真なら有効 |
| 既定 | 未設定・`"true"`・`"1"`・空文字 → 有効（現行動作） |
| 判定のタイミング | 🔴**モジュール定数にせず、`startup_event()` / `shutdown_event()` の中で毎回読む**（テストで `monkeypatch.setenv` が効くようにする） |
| 分岐する | `scheduler.start()`（L56）／`check_and_run_batch()`（L58）／`scheduler.shutdown()`（L63） |
| 分岐しない | `init_db()`・`init_user(crud)` |
| ログ | 無効時は `logger.info("Scheduler disabled (ENABLE_SCHEDULER=false)")` を startup で出す。`"Scheduler started"`／`"Scheduler stopped"` は有効時のみ |

判定は関数 `_scheduler_enabled()` に切り出し、3箇所で共用する（startup と shutdown で判定がずれないようにするため）。

## 3. テスト（T-P3-16）

`tests/` に新規ファイルを追加し、TC-16-1〜16-6 を実装する。`scheduler.start` / `check_and_run_batch` / `scheduler.shutdown` / `init_db` / `init_user` は `main` モジュール上でモックに差し替え、呼び出し有無を検証する。`SchedulerNotRunningError` は TC-16-5 で「`false` 起動 → shutdown で例外が出ない」ことを確認する。

| ケース | 値 | 期待 |
|---|---|---|
| 16-1 | 未設定 | start と check_and_run_batch が呼ばれる |
| 16-2 | `"false"` | どちらも呼ばれない |
| 16-3 | `"False"`／`"FALSE"` | 同上 |
| 16-4 | `"true"`／`"1"`／`""` | true 扱い |
| 16-5 | `"false"` で startup → shutdown | 例外なし・`scheduler.shutdown` 未呼び出し |
| 16-6 | `"false"` | `init_db`・`init_user` は呼ばれる |

## 4. 制約（厳守）

- `.env` を読まない（cat／grep／dotenv 読み込みを含む）。テストの環境変数は `monkeypatch` で設定する。
- シークレット値・接続文字列を出力しない。
- `conftest.py` は変更しない（`DATABASE_URL` のダミー代入は test_design v0.7 で扱う）。
- `render.yaml` は変更しない。

## 5. 完了条件と報告

1. `pytest` が全件 passed（従来 90 + 新規。件数を報告）。確認前に `Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue` を実行する。
2. `git diff --stat` が `backend/main.py` ＋ 新規テスト1ファイルのみ。
3. 報告：変更後の `startup_event()` / `shutdown_event()` 全文、pytest の件数、diff stat。
4. commit は Takumi が確認してから（push は Takumi が実施）。
