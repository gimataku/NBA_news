# 7-A-13a-3：3文書を元の場所（`NBA_news/` 直下）へ戻す【Takumi様が手動実施】

> **2026-10-17 変更**：`NBA_news/` 直下は Claude Code の作業範囲（`app/`）の外のため、**Takumi様が手動で実施する**。下の「手順」を手動手順として使う。Claude Code に任せられるのは `app/` 内（`.env.example`・`docs/`）の修正のみ。

作成日：2026-10-17 ／ 主担当：Claude Code → Takumi様（確認・commit）
決定（Takumi様）：①移動先は **`NBA_news/` 直下**（`app/` の外）②直下に既存の `README.md`・`setup.md`（重複）は **`app/` 側の新版で上書き**。
> 13a-2 の B（直下の重複の扱い）は本決定で解決。A（`.env` の置き場所）は本作業と併せて実施する。

🔴 `.env` は読まない。コード・テスト・`render.yaml`・`batch.yml` は変更しない。**移動は `git mv` を使い履歴を保つ。**

## 手順
1. **事前確認**：`git status` がクリーンであること（13a の変更は commit 済み、またはまとめて扱うこと）を確認。直下の既存 `README.md`・`setup.md` の `diff`（`app/` 側との差分）を**報告用に記録**（上書き前の最後の確認。旧版は git 履歴に残る）。
2. **移動**：`app/CLAUDE.md`・`app/setup.md`・`app/README.md` → `NBA_news/`。直下に既存があるものは `git rm` 後に `git mv`（上書き）。**`.env.example` と `docs/` は動かさない**（依頼は3文書のみ。`.env.example` の置き場所は下記 4）。
3. **相対パスの修正**（3文書は `app/` の1階層上に移るため）：
   - `docs/…`（設計書参照）→ `app/docs/…`。`backend/…`・`frontend/…`・`logs/…` の記述が `app/` 基準なら `app/backend/…` 等へ。
   - `CLAUDE.md` のディレクトリツリー：`NBA_news/` 直下に `CLAUDE.md`・`README.md`・`setup.md`・`render.yaml`・`.github/workflows/batch.yml`、`app/` 配下に `backend/`・`frontend/`・`docs/`・`.env.example`（現位置のまま）となるよう直す。「`app/` の外」の注記は不要になる箇所を整理。
   - `setup.md`・`README.md` の `cd` 手順・コマンド（`cd app/backend` 等）がリポジトリルート起点になるよう直す。
4. **`.env` の置き場所（13a-2 A）**：`load_dotenv` の読み込み先を `config.py` 等で grep で確定し、`setup.md`・`README.md`・`.env.example`（冒頭コメント）を**1つに統一**。`.env.example` は `app/` のまま。確定した場所と根拠行を報告。
5. **参照元の修正**：`grep -rn "app/CLAUDE.md\|app/setup.md\|app/README.md" ` をリポジトリ全体（`docs/` 含む）で実行し、パス参照を新位置に直す。**過去の実施記録（`manufacturing_verification_log_p3.md` の履歴行など）は当時の事実なので書き換えない**（現行の手順・参照のみ直す）。
6. **13a の検証を再実行**：#1 grep（`SQLite|APScheduler|cron|Persistent Disk|Starter|_p2_|/api/fetch`）／#2 旧記述 0 件／#3 シークレット混入なし／#5 3文書の整合／#5b `grep -n "\.env" CLAUDE.md` に禁止ルールが残っていること。加えて、文書中の**相対パス・ファイル名が新位置で実在する**ことを突合。

## 報告
1. `git status --short`（rename として検出されること）。
2. 上書きした直下ファイルの旧版との差分要約（旧記述が何だったか）。
3. 修正したパス記述の一覧、`.env` の確定位置と根拠。
4. 検証 #1〜#5b の結果。
5. commit は Takumi様。

---
## 最終配置（2026-10-17 確定）
`app/CLAUDE.md`（Claude Code が読むため `app/`）／`NBA_news/README.md`・`NBA_news/setup.md`（直下）。
**残作業（Claude Code 可・`app/CLAUDE.md` のみ）**：①ツリーを新配置に合わせる（`setup.md`・`README.md` を `NBA_news/` 直下へ、`CLAUDE.md` は `app/` のまま）②設計書参照パスは `app/CLAUDE.md` から見て `docs/…`（`app/docs/…` と書くと `app/` 起点で解決できない）。リポジトリルート起点で書くなら「パスはリポジトリルート起点」と明記。③`.env.example` は `app/` のまま。

## 手動実施用チェックリスト（Takumi様）
1. 直下の既存 `README.md`・`setup.md` は `app/` 側の新版で上書き（旧版は git 履歴に残る）。`git mv` で移動（`app/` 側は削除される）。
2. 移動後、各文書内のパスを直す：`docs/` → `app/docs/`、`backend/`・`frontend/` → `app/backend/`・`app/frontend/`（`cd` 手順を含む）。`CLAUDE.md` のツリーは `NBA_news/` 直下に3文書・`render.yaml`・`.github/`、`app/` 配下に `backend/`・`frontend/`・`docs/`・`.env.example` となるよう直し、「`app/` の外」注記を整理。
3. `.env` の置き場所を統一（`config.py` の `load_dotenv` の読み込み先に合わせる）。`app/` 内の `.env.example` の冒頭コメントは Claude Code に依頼可。
4. 🔴 **`CLAUDE.md` の「`.env` を読まない」ルールが残っていること**を確認。
5. **Claude Code の起動ディレクトリが `app/` でも、親の `NBA_news/CLAUDE.md` が読み込まれること**を確認（読まれない場合は起動位置を `NBA_news/` にするか、`app/` に1行の参照用 `CLAUDE.md` を置く）。
6. 検証：`grep -rn "app/CLAUDE.md\|app/setup.md\|app/README.md"`（現行手順内の旧パス参照が無いこと。過去の実施記録は除く）。
