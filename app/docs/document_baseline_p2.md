# ドキュメントベースライン（フェーズ2・本運用移行時点）

- **作成日**: 2026-08-23
- **目的**: 本運用移行時点の確定版ドキュメントを明示し、将来の改修時の参照基準とする
- **参照**: `docs/Project_Plan/project_plan_p2_v1.17.md` 手順11

---

## 1. 確定バージョン一覧

| ドキュメント | 確定ファイル名 | 格納場所 |
|---|---|---|
| 要件定義書 | `requirements_p2_v0.12.md` | `docs/Requirement/` |
| プロジェクト計画書 | `project_plan_p2_v1.17.md` | `docs/Project_Plan/` |
| リスク調査書 | `risk_report_p2_v0.9.md` | `docs/Risk_Report/` |
| 基本設計書 | `basic_design_p2_v0.5.md` | `docs/Basic_Design/` |
| 詳細設計書 | `detail_design_p2_v0.4.md` | `docs/Detail_Design/` |
| テスト設計書 | `test_design_p2_v0.2.md` | `docs/Test_Design/` |
| リスク評価書（最終） | `risk_report_final_p2_v1.4.md` | `docs/Risk_Report/` |
| セキュリティレビュー結果 | `security_review_p2_v1.0.txt` | `docs/Risk_Report/` |
| 製造着手前確認指示書 | `pre_manufacturing_checklist_p2.md` | `docs/Project_Plan/` |
| トレーサビリティマトリクス | `traceability_matrix_p2_v1.2.md` | `docs/Project_Plan/` |
| 製造動作確認・レビュー記録 | `manufacturing_verification_log_p2.md` | `docs/Project_Plan/` |
| 手動確認チェックリスト | `manual_check_p2_v1.1.md` | `docs/Test_Design/` |
| 週次確認チェックリスト（テンプレート） | `trial_weekly_checklist_p2_v1.1.md` | `docs/Trial/` |
| トライアル実施記録（第1回） | `trial_weekly_checklist_p2_v1.1_0705.md` | `docs/Trial/` |
| トライアル実施記録（第2回） | `trial_weekly_checklist_p2_v1.1_0711.md` | `docs/Trial/` |
| トライアル実施記録（第3回） | `trial_weekly_checklist_p2_v1.1_0718.md` | `docs/Trial/` |
| レビュー管理表 | `review_management.md` | `docs/Project_Plan/` |
| ドキュメントベースライン（本書） | `document_baseline_p2.md` | `docs/` |

> **注記：** ソースコード一式（`backend/` `frontend/`）・`setup.md`・`README.md`・`CLAUDE.md`・テストファイル一式（`backend/tests/`）も本運用移行時点の確定版として扱う。バージョン管理はGitにより行われている。

---

## 2. フェーズ2改修内容サマリー（changelog形式）

### 機能追加・変更

| # | 改修内容 | 対応要件 | 実装サブ手順 |
|---|---|---|---|
| 1 | カテゴリ再編（4分類：trade_fa / draft / injury / column） | F-01〜F-04 | 7-B, 7-G |
| 2 | 重複記事排除（Levenshtein距離80%閾値・`is_duplicate=1`） | F-07 | 7-A, 7-C |
| 3 | JWT認証機能（`POST /api/auth/login`・`useState`メモリ保持） | F-08, F-10 | 7-A, 7-D |
| 4 | 試合日程取得（`game_schedule`テーブル・BALLDONTLIE API） | C-05 | 7-A, 7-E |
| 5 | ネタバレ防止改修（`has_score`全カテゴリ対応・「スコアを隠す」ボタン F-05b） | F-05, F-05b | 7-B, 7-G |
| 6 | Render本番デプロイ（`host=0.0.0.0`・CORS環境変数化・Persistent Disk） | F-11 | 7-J-2, 7-J-3 |
| 7 | NBA公式順位リンク（`CategoryTabs.jsx`外部リンク追加） | F-12 | 7-K |

### インフラ変更（フェーズ1→フェーズ2）

| 区分 | フェーズ1 | フェーズ2 |
|---|---|---|
| 公開範囲 | ローカル限定（`host="127.0.0.1"`） | Render経由の限定公開（JWT認証付き） |
| データ永続化 | ローカルSQLite | Render Persistent Disk上のSQLite |
| 認証 | なし | JWT認証（SECRET_KEY・USERNAME・USER_PASSWORD） |
| カテゴリ数 | 旧6分類 | 新4分類（trade_fa/draft/injury/column） |

### テスト実績（手順8〜9）

| テスト種別 | 件数 | 結果 | カバレッジ |
|---|---|---|---|
| 単体テスト（手順8） | 80件 | 全件pass | 93% |
| 結合テスト（手順8.5） | 4件 | 全件pass | 94% |
| 総合テスト・自動（手順9） | 6件 | 全件pass | 94% |
| 手動確認（手順9） | 5シナリオ | OK（シナリオ3・8のUI部分はオフシーズンのため未確認） | — |

### トライアル運用実績（手順10）

| 確認日 | 翻訳品質 | 分類精度 | Claude API実績 | 月次合計 |
|---|---|---|---|---|
| 2026-07-05 | 5/5 | 5/5 | $1.27 | $8.54 |
| 2026-07-11 | 3/5 | 5/5 | $1.54 | $7.25 ⚠️ |
| 2026-07-18 | 3/5 | 5/5 | $1.72 | $8.97 |

> **⚠️ 数値要検証（2026-08-23・振り返りR-3指摘）**: 07-11行の月次合計$7.25は、Claude API実績$1.54＋Render固定費$7.25＝約$8.79であるべきところ、Render固定費のみが転記された疑いが強い。原典（週次チェックリスト`trial_weekly_checklist_p2_v1.1_0711.md` G章）も同値のため、記録時点での誤記と推定される。実績レンジは**約$8.5〜$9.0**として扱うこと。

全3回とも本運用移行基準（コスト・バッチ安定性・認証）をクリア。翻訳品質のNGは選手名表記ゆれに限定（意味は通じるレベル）。

---

## 3. 本運用移行時点の残課題

| # | 内容 | 対応時期 |
|---|---|---|
| 1 | シナリオ3（ネタバレぼかし表示）・シナリオ8（試合UI・スコア表示/隠すボタン）のフロントエンド目視確認 | 2026年10月NBAシーズン開幕後（初回週次確認 Section C で実施） |
| 2 | 選手名表記ゆれ（トライアル運用A-2 NG）の改善要否判断 | 必要と判断した場合に `processor/claude_client.py` のプロンプト修正 |
| 3 | セキュリティレビュー指摘の対応要否判断（🟡YEL-01〜04・🟢GRN-01〜04） | 短期（2026年9月まで）。**YEL-01は`config.py`3行追加で完結・即応推奨** |
| 4 | 死活監視の到達可能な方式への切り替え | 短期。現方式はサンドボックスのネットワーク制限でバックエンドに構造的に到達不可 |

> **残課題1はTakumi様2026-06-28承認済み**（オフシーズンのため開幕まで待機）。本運用移行の妨げとならない。

### 残課題3の内訳（`security_review_p2_v1.0.txt` より）

| ID | 内容 | 備考 |
|---|---|---|
| YEL-01 | `ANTHROPIC_API_KEY`／`BALLDONTLIE_API_KEY` が空でも起動する | `SECRET_KEY`のみRuntimeErrorを投げる非対称設計。設定漏れが「起動するが翻訳されない」故障になる |
| YEL-02 | `/api/auth/login` にレートリミットがない | 認証は著作権法第30条の公開範囲担保が主目的のため、**法的前提を崩すリスク**として再評価が必要 |
| YEL-03 | `/api/schedule` の日付パラメータに形式バリデーションがない | — |
| YEL-04 | `render.yaml` にPython/Nodeバージョンが未指定 | 7-J-2で対応済みか要確認 |
| GRN-01〜04 | 非推奨API・env変数名衝突・href未検証・CORS過剰許可 | 任意対応 |
