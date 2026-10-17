# 7-A-13b：プロジェクトドキュメント追従更新（後半）【Takumi様が手動実施】

作成日：2026-10-18 ／ 前提：7-A-6・7・8 完了。`NBA_news/README.md`・`setup.md` は Claude Code の作業範囲（`app/`）の外のため、**Takumi様が下記を貼り付ける**。`app/CLAUDE.md` は反映済み（件数 138・フロントのテスト手順・記述規約）。

## 1. `NBA_news/setup.md` の「6. テストの実行」を差し替える
現行の末尾の1行「2026-10-17 時点で 133 passed。…」を次に置き換え、フロントエンドの小節を続ける：

```markdown
2026-10-18 時点で 138 passed。`test_crud.py::test_t10_delete_old_articles` は秒境界で失敗することがある（既知・本番コードは正しい）。

### フロントエンドのテスト

`app/frontend/` ディレクトリから実行する（初回は `npm install` が必要）：

```
npm test          # テスト実行（vitest）
npm run test:cov  # カバレッジ付き（coverage/ に出力。Git 管理外）
```

テストは `app/frontend/src/__tests__/` に置く。記述規約：クラス名・`▶`/`▼` の記号・CSS をアサートしない／要素は `getByRole`・`getByText` で取る／`data-testid` は最後の手段。
```
（コードブロックの入れ子で崩れる場合は、外側を `~~~` にするなど貼り付け先の書式に合わせる）

## 2. `NBA_news/README.md`
「技術スタック」表のフロントエンド行に **`Vitest / Testing Library`（テスト）** を追記。「セットアップ」または「テスト」の節に次の1〜2行を追記（節が無ければ「起動方法」の後に「## テスト」を新設）：

```markdown
- バックエンド：`app/backend` から `pytest`（`DATABASE_URL` を外して実行）
- フロントエンド：`app/frontend` から `npm test`／`npm run test:cov`
詳細は [setup.md](./setup.md) を参照してください。
```

## 3. 最終 grep（PowerShell・リポジトリルートで実行）
`app/docs/` の過去の記録は対象外にするため、`docs` を除く：
```powershell
cd C:\Users\gimatakumi\Documents\projects\NBA_news
Select-String -Path README.md,setup.md,app\CLAUDE.md -Pattern "133 passed|チームのみ|cron方式は使用しない|Starter|Persistent Disk（1GB|app/backend/\.env|detail_design_p2|basic_design_p2|requirements_p2" 
```
期待：**0 件**（「Persistent Disk なし」のような否定の言及と、`app/backend/.env` が「誤り」として出てくる箇所が無いこと）。出た場合は内容を教えてください。

## 4. 完了条件
- [ ] setup.md に件数 138・フロントのテスト手順がある
- [ ] README.md にフロントのテスト手順（または setup.md への参照）がある
- [ ] 上記 grep が 0 件
- [ ] 完了後、計画書 v3.8 の 7-A-13 を ✅、7-A 全体を完了にする（私が更新）

> 資格情報の変更手順（Shell 不要）・週次チェックリストは **7-B** で整備する。GLOSSARY の運用（観測値の記録）も週次チェックリスト側。
