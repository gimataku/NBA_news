# 実装指示 7-A-8：フロントエンドのテスト基盤導入

作成日：2026-10-18 ／ 主担当：Claude Code ／ 根拠：テスト設計書 v0.6 §1-3（設定）・§1-4（記述規約）・§9 #7/#9/#11/#12、T-P3-13
🔴 `.env` は読まない。作業は `app/frontend/` 内のみ。**ルートの `.gitignore` は触れない**（`frontend/.gitignore` に追記する）。

## 1. 導入するパッケージ
```
cd app/frontend
npm i -D vitest @vitest/coverage-v8
npm i -D jsdom @testing-library/react @testing-library/dom @testing-library/jest-dom @testing-library/user-event
```
- 🔴 **`vitest` と `@vitest/coverage-v8` は同じコマンドで同時に導入し、同一バージョンにする**。**版番号を指定しない**（5日でメジャー版が上がった実績あり。テスト設計書§1-3）。
- `@testing-library/react` v16 は **`@testing-library/dom` を peer として要求する**ため併せて導入する（上記に含めた）。
- 🔴 **`--force`／`--legacy-peer-deps` を使わない**。peer 依存の警告・エラーが出たら**そのまま報告して止まる**。
- 導入後、実際に入った版（`vitest`・`@vitest/coverage-v8`・`@testing-library/react`・`react`・`vite`）を `npm ls` で確認し報告する。**`vitest` の peer が `vite ^8` を含むこと**、**`@testing-library/react` の peer が `react ^19` を含むこと**を `npm view <pkg>@<導入版> peerDependencies` で確認し、テスト設計書の「確認済み」記述（§9 #12）と照合する。

## 2. 設定
**`vite.config.js`**：既存の `plugins`・`server.proxy` は**変更しない**。`test` ブロックを追記する：
```javascript
test: {
  environment: 'jsdom',
  globals: true,
  setupFiles: './src/setupTests.js',
  coverage: {
    provider: 'v8',
    reporter: ['text', 'json-summary'],
    include: ['src/utils/**', 'src/hooks/**', 'src/components/**', 'src/App.jsx'],
    exclude: ['src/main.jsx'],
  },
},
```
- 🔴 **`src/App.jsx` を `include` に明示する**（`utils`／`hooks`／`components` のどれにも一致しないため、`exclude` から外すだけでは計測されない。§1-3・§9 #7）。
- 🔴 **`envPrefix` を設定しない**（既定の `VITE_` のまま。緩めると環境変数がビルド成果物に埋め込まれてブラウザに配信される。§9 #11）。`grep -n envPrefix vite.config.js` が **0 件**であることを確認。
- `defineConfig` を `vite` から import している現行形式で `test` キーが型・実行上受理されるか確認する（**vitest 版によって `vitest/config` の `defineConfig` が必要な場合は、そのように変更して理由を報告**）。

**`src/setupTests.js`（新規）**：
```javascript
import '@testing-library/jest-dom';
```

**`package.json` の `scripts` に追加**：`"test": "vitest run"`・`"test:cov": "vitest run --coverage"`（既存のスクリプトは変更しない）。

**`frontend/.gitignore`**：`coverage` を追記（`json-summary` が `coverage/` に出力するため）。**`eslint.config.js`**：`globalIgnores(['dist'])` を `globalIgnores(['dist', 'coverage'])` に変更。

## 3. 動作確認用テスト（T-P3-13 を前倒しで実装）
`vitest run` は**テストが0件だと失敗する**ため、基盤の動作確認を兼ねて **T-P3-13（`FilterBar.jsx`・F-14）** を実装する。
- 配置：**`src/__tests__/FilterBar.test.jsx`**（`src/components/` 内に置かない＝カバレッジの `include` にテストファイル自身が入るのを避ける）。
- 先頭で `import { describe, it, expect, vi } from 'vitest'` を**明示的に import** する（`globals: true` でも ESLint の `no-undef` を避けるため。`globals: true` は Testing Library の自動クリーンアップに必要なので残す）。
- 記述規約（テスト設計書§1-4）：**クラス名でアサートしない**／要素は `getByRole`／`getByText` で取る／`data-testid` を使わない／ユーザー操作は `@testing-library/user-event`。

| ケース | 内容 |
|---|---|
| TC-13-1 | `FilterBar` を `spursOnly={false}` で描画 → ボタン名 `Spursのみ` が存在する |
| TC-13-2 | ボタン名 `全チーム` が存在する（据え置き） |
| TC-13-3 | `spursOnly={false}` のとき `Spursのみ` ボタンをクリック → `onToggleSpurs` が1回呼ばれる（`vi.fn()`）。**`全チーム` は `spursOnly={false}` では disabled のため、クリック対象にしない** |

props は `FilterBar` の現行シグネチャ（`spursOnly`・`spoilerGuard`・`onToggleSpurs`・`onToggleSpoiler`）に合わせる。**`FilterBar.jsx` 本体は変更しない。**

## 4. 検証
| # | 確認 | 期待 |
|---|---|---|
| 1 | `npm test` | TC-13-1〜3 の3件が passed |
| 2 | `npm run test:cov` | 成功し、テキストのレポートに **`App.jsx` の行が現れる**（0% でよい。**現れなければ `include` の設定を見直す**。§9 #7）。`FilterBar.jsx` のカバレッジを報告 |
| 3 | `npm run build` | 成功（**ビルド成果物に `vitest`／テスト関連が混入していないこと**を `dist/` の存在確認で足りる範囲で） |
| 4 | `npm run lint` | エラー 0（新規ファイル由来の指摘がないこと。**既存の指摘があれば区別して報告**） |
| 5 | `grep -n envPrefix vite.config.js` | 0 件 |
| 6 | `git diff --stat` | `package.json`・`package-lock.json`・`vite.config.js`・`eslint.config.js`・`.gitignore`（frontend）・`src/setupTests.js`・`src/__tests__/FilterBar.test.jsx` のみ（**`App.jsx` ほか既存の `src/` は無変更**） |
| 7 | バックエンドの `pytest`（`DATABASE_URL` を外す） | 138 passed のまま（フロントの変更が影響しないことの確認） |

## 5. 報告
1. 導入された版と peer 確認結果／2. `vite.config.js` の diff 全文／3. 検証 #1〜#7／4. `test:cov` のレポート（`App.jsx`・`FilterBar.jsx` の行）／5. 警告・非推奨・脆弱性（`npm audit` の件数は**報告のみ**。`npm audit fix` は実行しない）／6. 設計書と実物の食い違い（`defineConfig` の import 先など）。
commit は Takumi様。**push するとフロントの静的サイトが再ビルドされる**ため、Render の Static Site のビルドが成功することを Takumi様が確認する（devDependencies 追加後も `npm run build` が通ることが前提）。
