# 実装指示 7-A-13a-2：13a の積み残し2件（調査→報告。変更は報告後）

作成日：2026-10-17 ／ 主担当：Claude Code ／ 前提：13a 完了（検証 #1〜#6 ✅）

🔴 `.env` は読まない（CLAUDE.md の規則どおり）。コード・テストは変更しない。

## A. `.env` の置き場所の食い違い
`setup.md` は `app/backend/.env`、`README.md` は `app/` で `cp .env.example .env`。**実物で正しい場所を確定する**。
1. `config.py`・`main.py`・`scheduler.py`・`run_batch_once.py` 等の `load_dotenv(...)` 呼び出しを grep し、**読み込むパス**（引数・既定の探索）を報告する。
2. 起動コマンドの作業ディレクトリ（`setup.md` の手順では `app/backend` から起動）で、そのパスが解決する場所を確定する。
3. 確定した場所に合わせて **`setup.md`・`README.md`・（必要なら）`.env.example` の冒頭コメント**を統一する。コードが両方の場所を許す場合は、推奨を1つに絞って書く。

## B. リポジトリルート（`NBA_news/`）の `README.md`・`setup.md`
1. 存在と更新日時、`app/` 配下のものとの差分（`diff`）を報告する。
2. 内容が旧記述（SQLite／Persistent Disk／Starter／cron 不使用／p2 設計書）かを 13a の grep で確認し、**一覧で報告**する。
3. **この時点では変更しない。** 重複なのか別目的なのかを報告し、Takumi様が方針（削除／app/ 側への参照化／同期）を決める。

## 検証・報告
- A：確定したパスの根拠（該当行）と、修正した箇所の一覧。
- B：差分と旧記述の残存一覧。
- `git diff --stat`：A の修正は文書のみ（`app/` の3文書＋必要なら `.env.example`）。
