# 詳細設計書（フェーズ3）

- **バージョン**: v0.4
- **ステータス**: Draft
- **作成日**: 2026-09-01
- **対象**: NBAニュース翻訳アプリ 改修（フェーズ3）手順4
- **参照**:
  - 要件定義書（フェーズ3）§1-2 F-13〜F-21
  - 基本設計書（フェーズ3）§2〜§6・**§8 引き継ぎ事項**
  - リスク調査書（フェーズ3）§1-4-8・§1-4-9・§4-2-1
  - プロジェクト計画書（フェーズ3）手順4・§8-0-3
  - 詳細設計書 v0.4（`detail_design_p2_v0.4.md`）※フェーズ2最終版・差分ベース
  - レビュー結果報告書（`review_detail_design_p3_v0.1.txt`。🔴1件・🟡0件・🟢3件／全件解消済み）
  - レビュー結果報告書（`review_detail_design_p3_v0.2.txt`。🔴0件・🟡0件・🟢3件／全件解消済み）
  - レビュー結果報告書（`review_detail_design_p3_v0.3.txt`。🔴0件・🟡0件・🟢1件）
  - レビュー結果報告書（`review_test_design_p3_v0.2.txt`。TD-R-01 が本書§2-4-1・§2-6 への差し戻しを含む）

---

## 0. 本書の範囲と方針

### 0-1. 設計対象

| 区分 | 対象 | 本書での扱い |
|---|---|---|
| **実装仕様** | F-13〜F-21の関数シグネチャ・型・処理フロー・擬似コード | ✅ §1〜§2 |
| **差分設計の実装仕様** | 要望1採用時の新規ファイル・変更ファイル | ✅ §3（**採否は手順6**） |
| **エラーハンドリング** | 新規・変更モジュールの異常系 | ✅ §4 |
| 設計判断そのもの | 方式の採否・閾値の決定 | ❌ 基本設計書で確定済み。**本書では変更しない** |
| テストケース | 単体・結合の観点と期待値 | ❌ 手順5（テスト設計・並走） |

> **本書の位置づけ**: 基本設計書は「**何をどう作るか**」を決めた。本書は「**実装者がそのまま書けるところまで具体化する**」。設計判断を蒸し返さず、**基本設計書の決定を実装の言葉に翻訳する**ことに徹する。

### 0-2. 基本設計書§8 引き継ぎ事項の消化状況

**13件すべてを追跡する。**

| # | 引き継ぎ先 | 内容 | 本書での状態 | 該当節 |
|---|---|---|---|---|
| 1 | 手順4 | Levenshtein の JS 実装（動的計画法・外部ライブラリなし） | ✅**確定** | §1-2 |
| 2 | 手順4 | `datetime.now(timezone.utc)` 置換時の比較処理の精査（naive/aware） | ✅**確定**（比較箇所なし・影響なしを確認） | §2-3 |
| 3 | 手順4 | `slowapi` の導入方法と `requirements.txt` への追加 | ✅**確定** | §2-1-1・§2-7 |
| 4 | 手順5 | `/api/fetch` 関連テストの削除 | ⏭️**削除対象を特定**（実際の削除は手順5・採否確定後） | §3-5 |
| 5 | 手順5 | 移行採用時のテストDBの扱い | ⏭️**手順5** | §6 #2 |
| 6 | 手順6 | 要望1の最終採否＋コスト基準の再定義 | ⏭️**手順6** | — |
| 7 | 手順7 | 週次チェックリストのフェーズ3版への改訂 | ⏭️**手順7** | — |
| 8 | **先-1（2026年9月まで）** | §5-5の設計を反映（`config.py` の用途別分離） | ✅**実装仕様を確定** | §3-2 |
| 9 | 手順5 | Levenshtein JS実装のテスト | ⏭️**手順5**（本書は関数境界を提示） | §1-2・§6 #1 |
| 10 | 手順4 | `uvicorn.run()` への `forwarded_allow_ips="*"` の追加 | ✅**確定**（#3と一体で設計） | §2-4-2 |
| 11 | **手順6の後** | 外部cron監視サービスの選定と ping 処理の実装 | ⏭️**手順6の後**（本書は**ping の呼び出し位置のみ**を確定） | §3-1 |
| 12 | 手順5 | Python側とJS側のLevenshtein値の一致を確認するテスト | ⏭️**手順5**（本書は**照合用の数値例**を提示） | §1-2-3 |
| 13 | 手順4 | `run_batch_once.py` の成否判定の実装 | ✅**確定**（判定位置・終了コード） | §3-1 |

> **⏭️ の6件について**: #4・#5・#6・#7・#11 は**手順4より後の工程が引き継ぎ先**であり、本書で確定させないことが正しい。#9・#12 は手順5（テスト設計）が引き継ぎ先だが、**テストが書けるだけの関数境界と数値例を本書で提示する**（手順5で仕様を推測させない）。

### 0-3. 要望1（無料化）の採否依存の所在

計画書§3 手順4より、**手順6（採否）は手順4より後**である。したがって**設計は先行し、実際の変更は採否確定後**とする。

| 節 | 採否依存 | 採否確定前にできること |
|---|---|---|
| §1 フロントエンド詳細設計 | **依存しない** | すべて実装可 |
| §2 バックエンド詳細設計 | **依存しない** | すべて実装可 |
| **§3 差分設計** | **採用時のみ** | **設計まで**。ファイル作成・既存ファイルの変更は採否確定後 |
| §3-2 `config.py` の用途別分離 | **依存しない** 🆕 | **先-1（2026年9月まで）に実施**。要望1が不採用でも価値がある（リスク調査書§4-2-2） |

> **§3-2 だけが例外である**。§3の中にあるが**採否に依存しない**。リスク調査書§4-2-2が「先-1の実施前に決定する」としたため§3に置いているが、**要望1が不採用でも実施する**。

---

## 1. フロントエンド詳細設計

### 1-1. `hooks/useNews.js`（変更）

#### 1-1-1. 追加する状態

基本設計書§2-1の3状態のうち、**`revealedIds`（L21）は変更しない**。以下2件を追加する。

```javascript
// 追加（F-13）
const [expandedIds, setExpandedIds] = useState(new Set());
// 追加（F-13・F-15 派生仕様b）: 親記事ID -> その関連ニュース欄で展開中の記事IDの集合
const [relatedExpandedIds, setRelatedExpandedIds] = useState(new Map());
```

| 状態 | 型 | 初期値 | 永続化 |
|---|---|---|---|
| `expandedIds` | `Set<number>` | 空Set | **なし**（要件定義書§2-1-1 項目4：メモリ上のみ） |
| `relatedExpandedIds` | `Map<number, Set<number>>` | 空Map | なし |
| `revealedIds`（既存） | `Set<number>` | 空Set | なし |

> **`localStorage` / `sessionStorage` は使用しない**。フェーズ2でJWTをメモリ保持（`useState`）とした方針を維持する（要件定義書§2-1-1 項目4の根拠）。

#### 1-1-2. 追加する操作関数

基本設計書§2-2の表をそのまま実装する。**一覧側の折りたたみだけが3つの状態すべてに触れる**。

```javascript
// 一覧側の展開/折りたたみ（F-13）
const toggleExpand = (id) => {
  setExpandedIds((prev) => {
    const next = new Set(prev);
    if (next.has(id)) {
      next.delete(id);
      // --- 折りたたみ時の副作用（基本設計書§2-2 1行目） ---
      // ① 関連ニュース欄の展開状態を破棄（文脈が切れる／Mapの単調増加を防ぐ）
      setRelatedExpandedIds((prevMap) => {
        if (!prevMap.has(id)) return prevMap;   // 変化がなければ同一参照を返す
        const nextMap = new Map(prevMap);
        nextMap.delete(id);
        return nextMap;
      });
      // ② 親記事自身のスコア表示状態のみリセット（要件定義書§2-1-2 確認事項5）
      //    関連ニュース内で表示した記事のIDには触れない（同§2-3-2 派生仕様d）
      resetSpoiler(id);
    } else {
      next.add(id);
    }
    return next;
  });
};

// 関連ニュース欄内の展開/折りたたみ（F-15 項目7：インライン展開）
const toggleRelatedExpand = (parentId, childId) => {
  setRelatedExpandedIds((prev) => {
    const next = new Set(prev.get(parentId) ?? []);
    next.has(childId) ? next.delete(childId) : next.add(childId);
    const nextMap = new Map(prev);
    next.size === 0 ? nextMap.delete(parentId) : nextMap.set(parentId, next);
    return nextMap;
  });
  // revealedIds には触れない（基本設計書§2-2 2行目：関連ニュース内の折りたたみではリセットしない）
};
```

> **⚠️ `toggleExpand` の副作用が `setExpandedIds` の更新関数の中にある点**: React の更新関数は StrictMode の開発ビルドで**2回呼ばれる**。`setRelatedExpandedIds` / `resetSpoiler` はいずれも**冪等**（削除操作）であるため2回実行されても結果は同じである。**副作用が冪等であることが前提**であり、将来ここに非冪等な処理を足してはならない。
>
> **代替案**: 副作用を更新関数の外（`expandedIds.has(id)` を読んで分岐）に出す書き方もあるが、その場合クロージャが古い `expandedIds` を掴む可能性がある。**冪等性が保証できる限り現在の形を採る。**

#### 1-1-3. `apiStatus` の拡張（F-なし・運用設計§6-1）

`/api/status` が `metrics` を返すようになる（§2-2-2）。既存の3項目は**キー名・意味とも変更しない**。

```javascript
const [apiStatus, setApiStatus] = useState({
  api_limit_exceeded: false,
  is_fallback: false,
  last_fetched_at: null,
  metrics: null,          // 追加。未取得・旧APIのときは null
});
```

> **`metrics` を画面に出すかは本フェーズの要件ではない**。要件定義書§4-1の運用指標は**週次チェックリストでの確認**が用途であり、`/api/status` を直接叩いて読む。フックが受け取って保持するところまでを本書の範囲とする。

#### 1-1-4. 戻り値の追加

```javascript
return {
  ...（既存の13項目は変更しない）,
  expandedIds,
  relatedExpandedIds,
  toggleExpand,
  toggleRelatedExpand,
};
```

### 1-2. `utils/levenshtein.js`（新規・F-15）

基本設計書§3-4の式をそのまま実装する。**外部ライブラリを追加しない**（§8 #1）。

#### 1-2-1. 実装

```javascript
/**
 * python-Levenshtein の ratio() と同一定義の類似度を返す。
 *   置換コスト 2 の編集距離 ldist を求め、
 *   ratio = (len(a) + len(b) - ldist) / (len(a) + len(b))
 * 素朴な実装（1 - distance / max(len)）とは値が異なる（基本設計書§3-4）。
 *
 * @returns {number} 0.0〜1.0
 */
export function ratio(a, b) {
  const s = a ?? '';
  const t = b ?? '';
  const m = s.length;
  const n = t.length;
  const lensum = m + n;
  if (lensum === 0) return 1.0;      // ratio("", "") === 1.0（python-Levenshtein と同じ）
  if (m === 0 || n === 0) return 0.0; // ldist = lensum となるため

  // 1行だけ保持する動的計画法（O(min(m,n)) メモリ）
  let prev = new Array(n + 1);
  let curr = new Array(n + 1);
  for (let j = 0; j <= n; j++) prev[j] = j;

  for (let i = 1; i <= m; i++) {
    curr[0] = i;
    const cs = s[i - 1];
    for (let j = 1; j <= n; j++) {
      const sub = prev[j - 1] + (cs === t[j - 1] ? 0 : 2); // ← 置換コスト2
      const del = prev[j] + 1;
      const ins = curr[j - 1] + 1;
      curr[j] = Math.min(sub, del, ins);
    }
    [prev, curr] = [curr, prev];
  }
  return (lensum - prev[n]) / lensum;
}
```

| 項目 | 設計 |
|---|---|
| 比較の正規化 | **`toLowerCase()` を呼び出し側で適用する**（`dedup.py` L24 と同じ扱い）。本関数は正規化しない |
| 文字単位 | **UTF-16 コードユニット単位**（`String.prototype.length` と `[]` の既定）。§1-2-2 参照 |
| 計算量 | O(m×n)。タイトルは50〜100文字程度、比較は最大49回のため**1展開あたり最大約50万回の内側ループ**。JavaScript で数ミリ秒（要件定義書§6 項目2の閾値200msに対して十分） |

#### 1-2-2. ⚠️ サロゲートペアの扱い

**Python の `str` はコードポイント単位、JavaScript の `String` は UTF-16 コードユニット単位である。**

| 対象 | Python `len()` | JavaScript `.length` |
|---|---|---|
| `"NBAドラフト"` | 7 | 7（BMP内のため一致） |
| 絵文字・一部の記号（サロゲートペア） | 1 | **2** |

> **本アプリでは実質的に一致する**。比較対象は `title_ja`（日本語）であり、日本語の文字・英数字・一般的な記号は**すべてBMP内（サロゲートペアにならない）**。ニュースのタイトルに絵文字が入る可能性は低い。
>
> **`[...s]` によるコードポイント分割を採らない根拠**: 配列化のコストが毎回発生し、**発生見込みの低いケースのために全比較を重くする**。仮に混入しても影響は当該ペア1文字ぶんの距離差であり、閾値判定を覆す規模ではない。
>
> **手順5への引き継ぎ**: Python側とJS側の一致テスト（§8 #12）は**BMP内の文字列で行う**。サロゲートペアを含むケースは**期待値が異なることが正しい**ため、テストケースに含めない（含めるなら「異なること」を期待値とする）。

#### 1-2-3. 手順5のための照合用数値例（§8 #12）

**Python側とJS側で同じ値が出ることを確認するための入力と期待値**を本書で確定する。

| # | a | b | ldist（置換コスト2） | 期待 `ratio` |
|---|---|---|---|---|
| 1 | `"NBA"` | `"NBAドラフト"` | 4 | **0.600** |
| 2 | `""` | `""` | 0 | **1.000** |
| 3 | `"abc"` | `""` | 3 | **0.000** |
| 4 | `"abc"` | `"abc"` | 0 | **1.000** |
| 5 | `"abc"` | `"abd"` | 2 | **0.667**（(3+3−2)/6） |
| 6 | `"kitten"` | `"sitting"` | 5 | **0.615**（(6+7−5)/13） |

> **#5 は素朴な式と偶然一致する**。素朴な式（置換コスト1・`1 - d/max`）では 1−1/3 = **0.667** となり `ratio()` と同値になる。**差が出るのは #1（0.429 対 0.600）と #6（0.571 対 0.615）**であり、乖離が最も大きいのは **#1** である。手順5では**#1 を必ず含める**。 🔧（v0.2で訂正・レビューDD-R-03対応）
>
> **素朴な式の値（v0.2で再計算し確定）**
>
> | # | a / b | `ratio()`（置換コスト2） | 素朴な式（置換コスト1・`1-d/max`） | 差 |
> |---|---|---|---|---|
> | #1 | `"NBA"` / `"NBAドラフト"` | **0.600** | **0.429** | **0.171** |
> | #5 | `"abc"` / `"abd"` | 0.667 | 0.667 | 0（偶然一致） |
> | #6 | `"kitten"` / `"sitting"` | 0.615 | 0.571 | 0.044 |
>
> **v0.1 の誤り**: 「#1 は 0.571 対 0.600」と書いていたが、**`0.571` は #6 の素朴値**である。#1 の素朴値は **0.429**。主張の向き（#1 で乖離する）は正しく、**訂正により差はむしろ大きくなる**ため設計判断は変わらない。**ただしテスト設計書 TC-08-1 に転記済みのため同時に訂正する。**
>
> **`dedup.py` のテストケースを流用する場合の注意**: `dedup.py` は `title_original`（英語）を比較するが、F-15は `title_ja`（日本語）である。**関数の一致確認が目的**であり入力言語は問わないため流用してよい。

### 1-3. `utils/relatedness.js`（新規・F-15）

基本設計書§3-2の式をそのまま実装する。

#### 1-3-1. 定数

```javascript
export const GATE_RATIO       = 0.20; // タイトル類似度のゲート（基本設計書§3-2）
export const SCORE_THRESHOLD  = 0.35; // 表示閾値
export const MAX_RELATED      = 5;    // 表示件数（要件定義書§2-3-1 項目3）
export const RECENCY_SPAN_H   = 168;  // 時期近接が0になる経過時間（7日）
const W_CATEGORY = 0.2, W_RATIO = 0.6, W_RECENCY = 0.2; // 重み（合計1.0）
```

> **4定数を `export` する根拠**: 閾値0.35とゲート0.20は**トライアル運用（手順10）で調整する**（基本設計書§3-2）。調整対象を1ファイルの先頭に集め、**コード中に数値を直接書かない**。

#### 1-3-2. 比較に使う文字列と時刻

| 項目 | 設計 | 根拠 |
|---|---|---|
| 比較文字列 | **`(article.title_ja \|\| article.title_original).toLowerCase()`** | 基本設計書§3-3。`title_ja` が NULL のときは `title_original` にフォールバック |
| 時刻 | **`fetched_at`** | 要件定義書§2-3-3 基準3が `fetched_at` と規定。`published_at` は **nullable**（`models.py` L23）だが `fetched_at` は **NOT NULL**（同L24） |

> **⚠️ `fetched_at` の文字列形式と JS の `Date` パース**: `fetched_at` は `strftime("%Y-%m-%dT%H:%M:%S")` で生成され、**タイムゾーン指定子を持たない**（`crud.py`・`scheduler.py`）。`new Date("2026-09-01T12:00:00")` は ES2015以降、**ローカル時刻として解釈される**（UTCではない）。
>
> **本設計では問題にならない**。recency は**2記事の `fetched_at` の差**しか使わないため、両者が同じ規則で解釈される限り**差は正しい**。日本にサマータイムはなく、解釈のずれが差に混入する余地もない。
>
> **絶対時刻として使ってはならない**。`Date.now()` との差を取ると9時間ずれる。既存の `formatRelativeTime`（`NewsCard.jsx` L44-53）は `published_at` に対して `Date.now()` との差を取っているが、**本フェーズの改修対象外**であり本書では触れない（§6 #4 に記録）。

#### 1-3-3. 実装

```javascript
import { ratio } from './levenshtein';

function titleOf(a) {
  return (a.title_ja || a.title_original || '').toLowerCase();
}

/** 経過時間による減衰。0〜1。168時間（7日）で0になる線形減衰。 */
function recency(a, b) {
  const ta = new Date(a.fetched_at).getTime();
  const tb = new Date(b.fetched_at).getTime();
  if (Number.isNaN(ta) || Number.isNaN(tb)) return 0; // 不正値は近接なしとみなす
  const hours = Math.abs(ta - tb) / 3600000;
  return Math.max(0, 1 - hours / RECENCY_SPAN_H);
}

/** 2記事間の関連度スコア。0〜1。 */
export function relatednessScore(current, other) {
  const r = ratio(titleOf(current), titleOf(other));
  if (r < GATE_RATIO) return 0;                    // ← ゲート（基本設計書§3-2）
  const sameCategory =
    current.category && other.category && current.category === other.category ? 1 : 0;
  return W_CATEGORY * sameCategory + W_RATIO * r + W_RECENCY * recency(current, other);
}

/**
 * 表示リスト内から関連ニュースを選ぶ。
 * @param {Array}  articles 現在の表示リスト全件（カテゴリ・Spursフィルタ適用後）
 * @param {Object} current  展開中の記事
 * @returns {Array} スコア降順の上位 MAX_RELATED 件。該当なしなら空配列
 */
export function selectRelated(articles, current) {
  return articles
    .filter((a) => a.id !== current.id)            // 項目6：自分自身を含めない
    .map((a) => ({ article: a, score: relatednessScore(current, a) }))
    .filter((x) => x.score >= SCORE_THRESHOLD)     // 項目8：閾値未満は除外
    .sort((x, y) => y.score - x.score || x.article.id - y.article.id)
    .slice(0, MAX_RELATED)
    .map((x) => x.article);
}
```

| 論点 | 設計 | 根拠 |
|---|---|---|
| `category` が NULL の記事 | **同一カテゴリとみなさない**（両方NULLでも `sameCategory = 0`） | 翻訳失敗時に `category` は NULL になる（`scheduler.py` ⑤のフォールバック）。**NULL同士を「同じ分類」と扱うのは意味的に誤り** |
| 同点時の順序 | **`id` の昇順**で安定化 | `Array.prototype.sort` は ES2019以降 stable だが、**入力順に依存すると再描画で並びが変わりうる**。明示的に決める |
| `is_duplicate` の除外 | **不要** | `/api/news` が `crud.get_articles()` で `is_duplicate == 0` を既に除外している（`crud.py` L43。要件定義書§2-3-1 項目5の注記） |
| 算出のタイミング | **展開時に `useMemo` で1回**（§1-5） | 基本設計書§3-4：リクエスト時・フロントエンド算出 |

### 1-4. `components/NewsCard.jsx`（変更・F-13／F-15／F-20）

#### 1-4-1. props の変更

```javascript
export function NewsCard({
  article, spoilerGuard, isRevealed, onReveal, onHide,   // 既存（変更なし）
  // --- 追加 ---
  isExpanded,          // boolean : expandedIds.has(article.id)
  onToggleExpand,      // () => void
  articles,            // Array   : 表示リスト全件（F-15の算出範囲）
  relatedExpandedIds,  // Set<number> | undefined : この記事の関連ニュース欄の展開状態
  onToggleRelated,     // (childId) => void
  revealedIds,         // Set<number> : 関連ニュース内のネタバレ判定に使う
  isNested = false,    // 関連ニュース欄の中に描画されているか（派生仕様a）
})
```

> **`isNested` の役割**: 派生仕様a（展開の深さは1段階まで）を**props で表現する**。`isNested === true` のとき `RelatedNews` を描画しない。**`RelatedNews` 側で制御すると入れ子の深さが増えたときに破綻する**ため、カード側が自分の位置を知る形にする。

#### 1-4-2. 描画構造

基本設計書§2-4の構造図を実装に落とす。

```jsx
<div className="border rounded-lg p-4 mb-3 bg-white shadow-sm">
  <CategoryBadge category={article.category} />

  {/* --- F-13：タイトル行全体がクリック対象（基本設計書§2-3） --- */}
  <h2
    className="font-semibold text-sm mt-1 mb-2 flex items-start gap-1 cursor-pointer select-none"
    onClick={onToggleExpand}
    role="button"
    tabIndex={0}
    aria-expanded={isExpanded}
    onKeyDown={(e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onToggleExpand(); }
    }}
  >
    <span aria-hidden="true" className="text-gray-400">{isExpanded ? '▼' : '▶'}</span>
    <span>{article.title_ja || article.title_original}</span>
  </h2>

  {/* --- 展開時のみ：既存の二段展開ブロックをそのまま内包する --- */}
  {isExpanded && (
    <>
      {/* ここは現行 L66-90 のブロックを無改変で移設する（F-05/F-05b） */}
      ...
      {/* --- F-15：関連ニュース（1段階まで） --- */}
      {!isNested && !needsSpoiler && (
        <RelatedNews
          articles={articles}
          currentArticle={article}
          spoilerGuard={spoilerGuard}
          revealedIds={revealedIds}
          onReveal={onReveal}
          onHide={onHide}
          expandedChildIds={relatedExpandedIds}   /* Set<number> | undefined → §1-5で既定値を持つ */
          onToggleChild={onToggleRelated}
        />
      )}
    </>
  )}

  <MetaRow />   {/* F-20：§1-4-4 */}
</div>
```

| 項目 | 設計 | 根拠 |
|---|---|---|
| 記号 | **`▶`（折りたたみ）／`▼`（展開）** | 基本設計書§2-3 |
| 位置 | タイトルの**左**（カテゴリバッジの下・タイトル行の先頭） | 同上 |
| アニメーション | **なし** | 同上（実装を単純に保つ） |
| クリック対象 | **タイトル行全体**（`<h2>` に `onClick`） | 同上 |
| キーボード操作 | **Enter / Space で展開**・`role="button"`・`tabIndex={0}`・`aria-expanded` | `<h2>` はクリック可能要素ではないため、**マウス以外で操作できなくなる**。要件ではないが、既存の `<a>`（原文リンク）と操作性を揃える |
| `SpoilerOverlay` | **変更しない** | 基本設計書§2-4（フェーズ2で未検証のネタバレUIへの影響を最小化） |

> **既存 L66-90 を無改変で移設する根拠**: F-13は「**その外側に展開制御を被せる**」設計である（基本設計書§2-4）。ブロックの中身に手を入れると、要件定義書§2-1-4 の制約（Section C クローズ前の改修を避ける）の趣旨から外れる。**移設のみで、条件・構造・クラス名を変えない。**

#### 1-4-3. `RelatedNews` の描画条件

要件定義書§2-3-1 項目9 と基本設計書§3-5 をそのまま実装する。

```javascript
const needsSpoiler = spoilerGuard && article.has_score && !isRevealed;  // 既存 L56（変更なし）
// 関連ニュースは needsSpoiler が false のときだけ描画する
```

| 記事の状態 | `needsSpoiler` | 関連ニュース |
|---|---|---|
| `has_score = false` | false | ✅**描画する**（オフシーズンはこれが大半） |
| `has_score = true` かつ ネタバレ防止OFF | false | ✅描画する |
| `has_score = true` かつ ON かつ **未表示** | **true** | ❌**描画しない** |
| `has_score = true` かつ ON かつ **表示済み** | false | ✅描画する |
| **関連ニュース欄の中**（`isNested`） | — | ❌**描画しない**（派生仕様a） |

> **⚠️ 否定形で書く**（基本設計書§2-4 の訂正）: 条件を「スコア表示済みのみ描画」と書くと、`has_score = false` の記事は `revealedIds` に入らないため**永久に描画されない**。**`needsSpoiler` の否定**が正しい。既存の `needsSpoiler`（L56）をそのまま使うことで、この誤りが起きない形にする。

#### 1-4-4. F-20：外部リンクのスキーム検証

```javascript
// NewsCard.jsx 内のモジュールスコープに置く（コンポーネント外・再生成を避ける）
const SAFE_SCHEMES = ['http:', 'https:'];

function isSafeUrl(raw) {
  if (!raw) return false;
  try {
    return SAFE_SCHEMES.includes(new URL(raw).protocol);
  } catch {
    return false;   // 相対URL・不正な文字列は許可しない
  }
}
```

描画側（現行 L92-102 の置換）:

```jsx
<div className="text-xs text-gray-400">
  {article.source} · {formatRelativeTime(article.published_at)}
  {isSafeUrl(article.source_url) && (
    <>
      {' · '}
      <a href={article.source_url} target="_blank" rel="noopener noreferrer"
         className="text-blue-500 underline">原文を読む</a>
    </>
  )}
</div>
```

| 論点 | 設計 | 根拠 |
|---|---|---|
| 不正スキーム時 | **「原文を読む」の要素ごと描画しない** | 基本設計書§4-4（v0.3で確定）。プレーンテキスト表示だと**通常時と異なりURLが露出する** |
| 区切りの `·` | **リンクと一緒に消す** | リンクを消して区切りだけ残ると**末尾に `·` が浮く** |
| 判定方式 | **`new URL()` の `protocol`** | 自前の正規表現より確実。`javascript:`・`data:`・`vbscript:` をまとめて弾ける |
| 相対URL | **`false`（描画しない）** | `new URL()` は base なしの相対URLで `TypeError` を投げる。RSS由来の `link` は絶対URLであり、相対が来る時点で異常 |
| `rel` / `target` | **現行のまま**（`noopener noreferrer` / `_blank`） | 変更しない |

> **発火可能性は低い**（基本設計書§4-4）。RSS由来の `link` が `javascript:` になることは考えにくい。**発火したときの見た目を実装者に判断させない**ために本書で確定する。

### 1-5. `components/RelatedNews.jsx`（新規・F-15）

```jsx
import { useMemo } from 'react';
import { selectRelated } from '../utils/relatedness';
import { NewsCard } from './NewsCard';

// モジュールスコープの共有空Set（§1-7 と同じ定数を使う。毎回 new Set() を作らない）
import { EMPTY_SET } from '../utils/constants';

export function RelatedNews({
  articles, currentArticle, spoilerGuard, revealedIds,
  onReveal, onHide,
  expandedChildIds = EMPTY_SET,          // 🔧 v0.2：既定値（レビューDD-R-01 問題2対応）
  onToggleChild,
}) {
  const related = useMemo(
    () => selectRelated(articles, currentArticle),
    [articles, currentArticle],
  );

  if (related.length === 0) return null;   // 項目8：該当なしなら欄自体を描画しない

  return (
    <div className="mt-3 pt-3 border-t border-gray-200">
      <h3 className="text-xs font-medium text-gray-500 mb-2">関連ニュース</h3>
      {related.map((a) => (
        <NewsCard
          key={a.id}
          article={a}
          spoilerGuard={spoilerGuard}
          isRevealed={revealedIds.has(a.id)}   {/* 派生仕様d：スコア表示状態は共有 */}
          onReveal={onReveal}
          onHide={onHide}
          isExpanded={expandedChildIds.has(a.id)}
          onToggleExpand={() => onToggleChild(a.id)}
          isNested={true}                       {/* 派生仕様a：1段階まで */}
        />
      ))}
    </div>
  );
}
```

| 項目 | 設計 | 根拠 |
|---|---|---|
| 表示位置 | 展開した `summary_ja` の**下部** | 要件定義書§2-3-1 項目2 |
| 該当なし | **`null` を返し欄ごと描画しない** | 同 項目8 |
| クリック時 | **その場でインライン展開**（`NewsCard` を再帰的に使う） | 同 項目7 |
| スコア表示状態 | **`revealedIds` を共有**。`onReveal` / `onHide` も親から受け取ったものをそのまま渡す | 同§2-3-2 派生仕様d |
| 展開状態 | **`expandedChildIds`（親記事専用のSet）**。一覧側の `expandedIds` とは**別**  | 同 派生仕様b |
| **既定値** 🆕（v0.2） | **`expandedChildIds = EMPTY_SET`**（デフォルト引数） | **`undefined` は通常状態である**（下記）。受け側でも潰す |
| 深さの制御 | **`isNested={true}` を渡す**。子カードは `RelatedNews` を描画しない | 同 派生仕様a |
| 再計算 | **`useMemo`**。依存は `articles` と `currentArticle` | 展開のたびに最大49回の比較を繰り返さない |

> **`NewsCard` を再帰的に使う根拠**: 関連ニュース内でも**同じ二段展開（F-05/F-05b）が適用される**（派生仕様c）。専用の簡易カードを別に作ると、ネタバレ防止の挙動を**2箇所に実装することになる**。`isNested` 1つで深さを止められるため、再帰の危険もない。
>
> **循環 import について**: `NewsCard.jsx` → `RelatedNews.jsx` → `NewsCard.jsx` の循環が生じる。ES Modules は循環を解決できるが、**モジュール評価順によっては一方が未定義になりうる**。両ファイルとも**関数宣言（`export function`）**で定義し、参照は描画時（実行時）に限る形にすることで回避する。**アロー関数を定数に代入する形（`export const NewsCard = () => ...`）にしてはならない**（巻き上げが効かない）。

#### ⚠️ `expandedChildIds` が `undefined` になる経路（v0.2追加・レビューDD-R-01 問題2対応）

**「キーが無い」は例外ではなく通常状態である。**

`useNews.js` の `relatedExpandedIds` は `Map<number, Set<number>>` であり、§1-1-2 の `toggleRelatedExpand` は**展開中の子が0件になったらエントリごと削除する**。

```javascript
next.size === 0 ? nextMap.delete(parentId) : nextMap.set(parentId, next);
```

したがって `relatedExpandedIds.get(article.id)` は次の場合に `undefined` を返す。

| 場面 | 頻度 |
|---|---|
| **記事を初めて展開した瞬間** | **必ず**（親記事のエントリはまだ無い） |
| 関連欄の子をすべて折りたたんだ後 | 通常操作 |

v0.1 は本コンポーネントで `expandedChildIds.has(a.id)` を**無条件に参照**していた。既定値がなければ、**関連ニュースを持つ記事を最初に展開した時点**で次が発生する。

```
TypeError: Cannot read properties of undefined (reading 'has')
```

React のエラーバウンダリを置いていないため、**画面全体が白くなる**。

**対処：渡す側と受ける側の両方で潰す**

| 側 | 対処 | 節 |
|---|---|---|
| **渡す側**（`App.jsx`） | `relatedExpandedIds.get(article.id) ?? EMPTY_SET` | §1-7 |
| **受ける側**（本コンポーネント） | デフォルト引数 `expandedChildIds = EMPTY_SET` | 本節 |

> **両方で潰す根拠**: 渡す側だけだと、**将来 `App.jsx` 以外から `NewsCard` / `RelatedNews` を使ったときに再発する**。受ける側だけだと、`App.jsx` を読む人が「`undefined` を渡してよい」と気付けない。**片方で足りるが、両方あると壊れ方が減る**。
>
> **`EMPTY_SET` を定数にする根拠**: `?? new Set()` と書くと**毎描画で新しい参照が生まれる**。`NewsCard` を将来 `React.memo` で包んだとき、**props が毎回変わるためメモ化が効かなくなる**。`src/utils/constants.js` に `export const EMPTY_SET = new Set();` を置き、**両側が同じ参照を使う**。
>
> **⚠️ `EMPTY_SET` を変更してはならない**（`add` / `delete` を呼ばない）。共有オブジェクトであり、変更すると全箇所に波及する。読み取り専用として扱う。

### 1-6. `components/FilterBar.jsx`（変更・F-14）

| 箇所 | 変更前 | 変更後 |
|---|---|---|
| L24 | `チームのみ` | **`Spursのみ`** |
| L14 | `全チーム` | **変更なし** |

> **ロジックは一切変更しない**（要件定義書§2-2-2）。`spursOnly` の真偽・`onToggleSpurs`・API呼び出しはそのまま。**表示ラベル1箇所のみ**。

### 1-7. `App.jsx`（変更・F-13／F-15） 🆕（v0.2新設・レビューDD-R-01対応）

**v0.1 には本節がなく、F-13・F-15 が画面につながらなかった。**

#### 1-7-1. なぜ変更が必要か

`App.jsx` は **`NewsCard` を描画する唯一のファイル**である（`MainView` 内・L87-96）。

```
$ grep -n "NewsCard\|useNews" frontend/src/App.jsx
   2: import { useNews } from './hooks/useNews';
   7: import { NewsCard } from './components/NewsCard';
  51: } = useNews(token, logout);
  88: <NewsCard
  92:   isRevealed={revealedIds.has(article.id)}
```

| 本書が増やすもの | 件数 | 節 |
|---|---|---|
| `useNews` の**戻り値** | **4件**（`expandedIds`・`relatedExpandedIds`・`toggleExpand`・`toggleRelatedExpand`） | §1-1-4 |
| `NewsCard` の **props** | **7件**（`isExpanded`・`onToggleExpand`・`articles`・`relatedExpandedIds`・`onToggleRelated`・`revealedIds`・`isNested`） | §1-4-1 |

**両者をつなぐコードは `App.jsx` L87-96 にしかない。** 本節がなければ `isExpanded` は `undefined` になり、§1-4-2 の `{isExpanded && (...)}` により**すべての記事が永久に折りたたまれたまま**になる。例外は出ないため、**「実装したのに何も起きない」**という形で現れる。

> **v0.1 が漏らした原因**: 基本設計書§1-2「コンポーネント一覧（フェーズ3の変更分）」11件に `App.jsx` が含まれておらず、本書はその一覧を出発点にした。**一覧に載っているものが正しいかは確認したが、載っていないものがないかを確認していなかった**。
>
> **一般化**（§5-2に判断項目を新設）: **戻り値や props を増やす設計では、その値を受け渡す中間の呼び出し元が一覧から落ちやすい。** `grep -rn '<変更するコンポーネント名>' src/` で呼び出し元を洗う。

#### 1-7-2. 変更内容

**① `src/utils/constants.js`（新規）**

```javascript
/** 共有の空Set。参照が毎回変わらないようモジュールスコープに置く（§1-5）。
 *  読み取り専用として扱い、add / delete を呼んではならない。 */
export const EMPTY_SET = new Set();
```

**② `useNews` の戻り値の受け取り（L38-51 の分割代入に4件追加）**

```javascript
const {
  articles, apiStatus, selectedCategory, spursOnly, spoilerGuard,
  revealedIds, loading, setSelectedCategory, toggleSpursFilter,
  toggleSpoilerGuard, revealScore, resetSpoiler,      // ← 既存12件は変更しない
  expandedIds,                                        // 🆕
  relatedExpandedIds,                                 // 🆕
  toggleExpand,                                       // 🆕
  toggleRelatedExpand,                                // 🆕
} = useNews(token, logout);
```

**③ `NewsCard` への受け渡し（L87-96 の置換）**

```jsx
articles.map((article) => (
  <NewsCard
    key={article.id}
    article={article}
    spoilerGuard={spoilerGuard}
    isRevealed={revealedIds.has(article.id)}
    onReveal={revealScore}
    onHide={resetSpoiler}
    /* --- ここから追加（§1-4-1） --- */
    isExpanded={expandedIds.has(article.id)}
    onToggleExpand={() => toggleExpand(article.id)}
    articles={articles}
    relatedExpandedIds={relatedExpandedIds.get(article.id) ?? EMPTY_SET}
    onToggleRelated={(childId) => toggleRelatedExpand(article.id, childId)}
    revealedIds={revealedIds}
    /* isNested は渡さない（既定 false。一覧側は入れ子ではない） */
  />
))
```

| 行 | 設計 | 根拠 |
|---|---|---|
| `isExpanded` | `expandedIds.has(article.id)` | `Set` から真偽へ変換するのは呼び出し側 |
| `onToggleExpand` | **引数なしの関数**にして `article.id` を閉じ込める | §1-4-1 の型（`() => void`）に合わせる。`NewsCard` に ID を再度渡さない |
| **`relatedExpandedIds`** | **`Map.get()` の結果に `?? EMPTY_SET`** | **`undefined` は通常状態**（§1-5）。ここが本節の要点 |
| `onToggleRelated` | `(childId) => toggleRelatedExpand(article.id, childId)` | `Map` のキー（親ID）を呼び出し側で閉じ込め、`NewsCard` は子IDだけを知る |
| `revealedIds` | **`Set` をそのまま渡す** | 関連ニュース欄が子記事のネタバレ判定に使う（派生仕様d・共有） |
| `isNested` | **渡さない** | §1-4-1 の既定値 `false`。一覧側は入れ子ではない |
| `ApiBanner`・`CategoryTabs`・`FilterBar`・`GameSchedule` | **変更しない** | 本フェーズの改修対象外 |

> **`Map` → `Set` の変換をここで行う根拠**（3案の比較）:
>
> | 案 | 変換の位置 | 採否 |
> |---|---|---|
> | **案A** | **`App.jsx`**（`.get() ?? EMPTY_SET`） | ✅**採用** |
> | 案B | `RelatedNews` に `Map` と `parentId` をそのまま渡し内部で変換 | ❌不採用 |
> | 案C | `useNews` 側で「キーが無ければ空Set」を返す形にする | ❌不採用 |
>
> **採用根拠**: 案Bは `NewsCard` の props 定義（§1-4-1：`Set<number> | undefined`）を変更することになり、**`NewsCard` が `Map` の構造（親IDによる階層）を知る**必要が生じる。`NewsCard` は一覧側でも関連欄の中でも使われるため、**自分がどちらにいるかに依存しない**方がよい（`isNested` 1つで済んでいる利点が失われる）。案Cは Proxy か getter 関数が要り、**フックの戻り値の型が複雑になる**。案Aは**変換が1箇所（呼び出し側）に収まり、既存の型定義を変えない**。

#### 1-7-3. ⚠️ `MainView` は export されていない

`App.jsx` の構造は次のとおりである。

| 関数 | export | 内容 |
|---|---|---|
| `App`（L27-35） | **`export default`** | `useAuth()` → 未認証なら `LoginForm`・認証済みなら `MainView` |
| `MainView`（L37-101） | **なし**（モジュール内部） | `useNews()` と記事一覧の描画。**本節の変更対象** |
| `ApiBanner`（L9-25） | なし | 変更しない |

**テストから `MainView` を直接描画できない。** 結線を検証するテスト（テスト設計書 T-P3-17）は **`App` を描画し、`useAuth` をモックして認証済み状態にする**必要がある。

| 案 | 内容 | 採否 |
|---|---|---|
| **`useAuth` をモックして `App` を描画** | テスト側だけで完結する | ✅**採用** |
| `MainView` を export する | テストのために本番コードの公開範囲を広げる | ❌不採用 |

> **`MainView` を export しない根拠**: 外部から使う予定がないものを、**テストのためだけに公開しない**。`useAuth` は既にフックとして分離されており、モックは容易である（`vi.mock('./hooks/useAuth')`）。**本番の構造をテストの都合で変えるのは、必要になってからでよい。**
>
> **本節を書く理由**: この制約を書いておかないと、手順8で「`MainView` が import できない」と気付いてから**本番コードを変えるか迷う**ことになる。**判断を先に済ませておく。**

---

## 2. バックエンド詳細設計

### 2-1. `api/routes.py`（変更）

#### 2-1-1. F-17：ログインのレートリミット

**`slowapi` を導入する**（基本設計書§4-1・§8 #3）。

**`api/limiter.py`（新規）** — **インスタンスはここだけで生成する。**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

> **独立モジュールに置く根拠**: `main.py` で生成して `routes.py` から import すると `main` → `routes` → `main` の**循環 import** になる。`api/limiter.py` は `slowapi` にしか依存しないため、**両方がそこから import すれば循環しない**。

**`main.py` 側**（アプリ生成箇所） 🔧（v0.3で訂正・レビューDD2-01対応）

```python
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.limiter import limiter          # ← 生成せず import する

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

> **`app.state.limiter` への代入と例外ハンドラの登録は `main.py` で行う**（アプリに紐づく設定のため）。**インスタンスの生成とは役割が違う。**

**`api/routes.py` 側** 🔧（v0.3で import を追記・レビューDD2-01対応）

```python
from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException,
                     Query, Request, status)        # ← L1 に Request を追加
from api.limiter import limiter                     # ← 追加
from config import LOGIN_RATE_LIMIT                 # ← 追加

@router.post("/auth/login")
@limiter.limit(LOGIN_RATE_LIMIT)          # "5/minute"
async def login(request: Request, body: LoginBody):
    ...（本体は変更しない）
```

> **⚠️ v0.2 のコードブロックは、直下の注記と食い違っていた**（レビューDD2-01）。注記は「`limiter` は独立モジュール（`api/limiter.py`）に置き、`main.py` と `routes.py` の両方がそこから import する」としていたが、**`main.py` のブロックは `limiter = Limiter(...)` を独自に生成していた**。**実装者はコードブロックを先に読む**ため、注記に正しいことが書いてあっても救いにならない。
>
> **二重生成で何が起きるか**（`slowapi` を実際に導入して確認）
>
> | 論点 | 結果 |
> |---|---|
> | `@limiter.limit()` の判定に使う限界値 | **デコレータ側の `limiter`**（`api.limiter` の実体）が数える |
> | `_rate_limit_exceeded_handler` | **`request.app.state.limiter._inject_headers(...)` を呼ぶ**（`app.state` 側を読む） |
> | `_inject_headers` の中身 | `if self.enabled and self._headers_enabled and ...` |
> | `Limiter._headers_enabled` の既定値 | **`False`** |
>
> **既定設定では実害が出ない**（`_inject_headers` は何もせずに返る）が、無害とは言い切れない。
>
> | # | 残る問題 |
> |---|---|
> | 1 | **テストと本番で構成が食い違う**。テスト設計書§2-0 #1／#3 は `api.limiter` の実体を `app.state.limiter` に設定し `limiter.reset()` でカウンタを初期化する。本番が別インスタンスを持つなら、**テストが検証しているのは本番と異なる構成**である。**これは TD-R-01 で是正したばかりの型**（テストが本番の実体を読んでいない）である |
> | 2 | 将来 `Limiter(..., headers_enabled=True)` にすると、`app.state` 側の**空のストレージから残り回数を計算**し、`X-RateLimit-Remaining` に誤った値を返す |
>
> **対処を入れておけば `slowapi` の版に依存しなくなる**（`_headers_enabled` の既定が将来変わっても影響しない）。
>
> **`Request` の追加も v0.2 では漏れていた**。`api/routes.py` L1 の `from fastapi import ...` に **`Request` は含まれていない**。`slowapi` のデコレータは引数名 `request` で `Request` を受け取る関数にしか適用できないため、**追加しないと `NameError` になる**。

| 項目 | 設計 | 根拠 |
|---|---|---|
| 適用対象 | **`POST /api/auth/login` のみ** | 基本設計書§4-1（他はJWT必須のため優先度が低い） |
| 制限値 | **`"5/minute"`**（`config.LOGIN_RATE_LIMIT`） | 同上 |
| キー | **`get_remote_address`**（IP単位） | 同上。**§2-4-2 の `forwarded_allow_ips` が前提** |
| 超過時 | **HTTP 429** | `_rate_limit_exceeded_handler` の既定 |
| ロックアウト | **なし** | 基本設計書§4-1（単一利用者のため本人を締め出すリスクの方が大きい） |

> **⚠️ `request: Request` を第1引数に加える必要がある**。`slowapi` のデコレータは**引数名 `request` で `Request` を受け取る関数にしか適用できない**（`key_func` が `request` から呼び出し元IPを取るため）。現行の `login(body: LoginBody)` のままでは `Exception: No "request" argument` で**起動時ではなくリクエスト時に失敗する**。

#### 2-1-2. F-18：日付パラメータのバリデーション

```python
from datetime import date

@router.get("/schedule")
async def get_schedule(
    start_date: date,                       # str → date（Pydantic/FastAPI が検証）
    end_date:   date,
    current_user: str = Depends(get_current_user),
):
    """C-05タブ用。game_scheduleテーブルから試合日程を返す。"""
    games = crud.get_game_schedule(start_date.isoformat(), end_date.isoformat())
    return {"games": games}
```

| 項目 | 設計 | 根拠 |
|---|---|---|
| 方式 | **型注釈を `datetime.date` にするだけ** | 基本設計書§4-2：独自バリデーション関数を書かずフレームワークに寄せる |
| 不正時 | FastAPI が自動的に **HTTP 422** | 同上 |
| **crud への受け渡し** 🆕 | **`.isoformat()` で `"YYYY-MM-DD"` 文字列に戻す** | `crud.get_game_schedule()`（L150）は `GameSchedule.game_date`（**TEXT・`"YYYY-MM-DD"`**）と直接比較する。`date` オブジェクトのまま渡すと**文字列とdateの比較になり結果が不定**になる |
| `crud` 側の変更 | **なし** | 型を境界（API層）で正規化し、**内側の層は変更しない** |

> **⚠️ `.isoformat()` を忘れると起きること**: SQLite では `date` オブジェクトが文字列化されて偶然動くが、**PostgreSQL（要望1採用時のNeon）では型不一致でエラーまたは想定外の結果になる**。要望1の採否に関わらず `.isoformat()` を入れる。
>
> **`start_date > end_date` の検証は行わない**。空配列が返るだけで害がなく、要件にもない。

#### 2-1-3. `/api/status` の拡張（運用設計§6-1）

```python
@router.get("/status")
async def get_status(current_user: str = Depends(get_current_user)):
    log = crud.get_latest_fetch_log()
    return {
        "last_fetched_at":    crud.get_setting("last_fetched_at"),      # 既存
        "source_used":        log["source_used"] if log else None,      # 既存
        "is_fallback":        log["is_fallback"] if log else False,     # 既存
        "api_limit_exceeded": crud.get_setting("api_limit_exceeded") == "true",  # 既存
        "metrics":            crud.get_metrics(),                       # 追加
    }
```

| 項目 | 設計 | 根拠 |
|---|---|---|
| 既存4項目 | **キー名・意味とも変更しない** | 週次チェックリスト・`useNews.js` が参照している |
| 追加 | **`metrics` オブジェクト1つ**（フラットに増やさない） | 既存と新規の境界を明示し、フロント側で `metrics == null` の分岐を書けるようにする |
| 認証 | **JWT必須のまま** | 基本設計書§6-1（記事件数・カテゴリ分布は利用実態を推測できる） |

#### 2-1-4. F-なし：`/api/fetch` の扱い

**本節では変更しない**（要望1採用時のみ削除。§3-5）。

### 2-2. `db/crud.py`（追加）

#### 2-2-1. 追加関数 `get_metrics()`

```python
def get_metrics() -> dict:
    """
    /api/status の metrics 用。要件定義書§4-1 の指標1・2・3・6・9 を返す。
    指標7（ERROR件数）・8（Disk使用量）はAPIでは扱わない（基本設計書§6-1）。
    """
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=METRICS_WINDOW_DAYS)
    ).strftime("%Y-%m-%dT%H:%M:%S")

    with SessionLocal() as session:
        total = (
            session.query(func.count(Article.id))
            .filter(Article.is_duplicate == 0).scalar()
        )
        last_7d = (
            session.query(func.count(Article.id))
            .filter(Article.is_duplicate == 0)
            .filter(Article.fetched_at >= cutoff).scalar()
        )
        by_category = dict(
            session.query(Article.category, func.count(Article.id))
            .filter(Article.is_duplicate == 0)
            .filter(Article.fetched_at >= cutoff)
            .group_by(Article.category).all()
        )
        duplicates = (
            session.query(func.count(Article.id))
            .filter(Article.is_duplicate == 1).scalar()
        )
        fallbacks = (
            session.query(func.count(FetchLog.id))
            .filter(FetchLog.is_fallback == 1)
            .filter(FetchLog.executed_at >= cutoff).scalar()
        )

    return {
        "total_articles":      total,
        "articles_last_7d":    last_7d,
        "by_category_7d":      {k: v for k, v in by_category.items() if k is not None},
        "duplicate_count":     duplicates,
        "fallback_history_7d": fallbacks,
    }
```

| 指標 | 定義 | 対応する要件定義書§4-1 |
|---|---|---|
| `total_articles` | `is_duplicate = 0` の全件 | 指標1 |
| `articles_last_7d` | 同・直近7日（`fetched_at >= cutoff`） | 指標2 |
| `by_category_7d` | 同・直近7日をカテゴリで集計 | 指標3 |
| `duplicate_count` | `is_duplicate = 1` の全件 | 指標9 |
| `fallback_history_7d` | `fetch_logs.is_fallback = 1` の直近7日の件数 | 指標6 |

| 論点 | 設計 | 根拠 |
|---|---|---|
| N（集計期間） | **7日**（`config.METRICS_WINDOW_DAYS`） | 基本設計書§6-1。週次チェックリストの周期と一致させる |
| `category` が NULL の記事 | **`by_category_7d` から除外する** | 翻訳失敗時に NULL になる。キーが `null` の項目は**JSONで扱いづらく、カテゴリ分布の読み取りを妨げる**。件数は `articles_last_7d` に含まれるため、差分から把握できる |
| 0件のカテゴリ | **キー自体が現れない** | `group_by` の結果をそのまま使う。週次チェックリストは「偏りの検知」が目的であり、0件は欠落として読める |
| セッション | **1つの `with` で5クエリ**を実行 | 接続の確立を1回に抑える。要望1採用時（Neon・CU課金）に効く |
| 集計方式 | **`func.count()` による集計クエリ** | 全件を Python 側に取り出して数えると、記事数の増加でメモリと転送量が増える |
| 生SQL | **使わない** | `crud.py` は全関数がSQLAlchemy ORM（生SQL 0件）。移行時の変更を1行に抑える方針（基本設計書§5）を崩さない |

> **追加 import** 🔧（v0.2で訂正・レビューDD-R-04対応）: `db/crud.py` L1-6 の実物と突き合わせた結果は次のとおり。
>
> | 行 | 現状 | 変更 |
> |---|---|---|
> | L3 | `from sqlalchemy import desc` | **`from sqlalchemy import desc, func`**（`func` を追加） |
> | L5 | `from config import DATA_RETENTION_DAYS` | **`from config import DATA_RETENTION_DAYS, METRICS_WINDOW_DAYS`**（追加） |
> | L6 | `from .models import AppSetting, Article, FetchLog, GameSchedule, SessionLocal, User` | **変更なし**（`FetchLog` は**既に import 済み**） |
>
> **v0.1 の誤り**: 「`FetchLog` を追加する」としていたが**L6 に既にある**。一方で **`METRICS_WINDOW_DAYS` の追加指示が欠けていた**（`get_metrics()` は本体でこれを参照する）。このまま実装すると `/api/status` の呼び出し時に **`NameError: name 'METRICS_WINDOW_DAYS' is not defined`** が発生する。
>
> **検出が遅れる種類ではない**（テスト設計書 T-P3-03 が `/api/status` を叩くため手順8の最初のテスト実行で必ず落ちる）が、本書は「実装者がそのまま書ける」ことを目的としており、**追加 import を明示する節でその1件が欠けている**のは目的に反する。**§5-1 の照合リストに `crud.py` L1-6 を追加**し、再発を防ぐ。

### 2-3. `auth/jwt.py`（変更・F-19）

```python
from datetime import datetime, timedelta, timezone   # timezone を追加

def create_access_token(data: dict) -> str:
    """JWTトークンを発行する（有効期限30日）"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)  # L11
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
```

#### ⚠️ naive/aware の精査結果（§8 #2）

**基本設計書§4-3が「比較処理がある場合は要確認」とした点を、実装を読んで確定させる。**

| 確認対象 | 結果 |
|---|---|
| `auth/jwt.py` 内で `expire` を**他の datetime と比較する箇所** | **存在しない**。`to_encode["exp"]` に入れて `jwt.encode()` に渡すのみ（L11-13） |
| `python-jose` の `exp` の扱い | `datetime` を受け取ると **`timegm(value.utctimetuple())` で UNIX 秒に変換**する。`utctimetuple()` は **aware なら UTC に正規化してから**タプル化するため、**naive（UTC想定）と aware（UTC）で同じ値になる** |
| `verify_token()` 側（L19） | `jwt.decode()` が**数値の `exp` と現在時刻を数値比較**する。datetime は介在しない |
| `auth/users.py`・`crud.py` の日時 | `datetime.now(timezone.utc)` を**文字列化して保存**しており、`utcnow()` は使っていない |

> **結論：影響なし。`datetime.now(timezone.utc)` への置換のみで完了する。** 追加の変換・比較の修正は不要である。

#### ⚠️ `utcnow()` の残存箇所（§5-1 A区分 [43] の結果）

**本番コード以外にもう1件ある。**

| 箇所 | 内容 | 扱い |
|---|---|---|
| `auth/jwt.py` L11 | `datetime.utcnow() + timedelta(...)` | ✅**本要件（F-19）で置換する** |
| **`tests/test_routes.py` L119** | `"exp": datetime.utcnow() - timedelta(hours=1)`（**期限切れトークンの生成**） | ⚠️**本書では置換しない**。§6 #11 で手順5へ引き継ぐ |

> **テスト側を本書で置換しない根拠**: F-19 の由来はセキュリティレビュー GRN-01（**本番コードの非推奨API**）である。テストコードは手順5（テスト設計）の担当範囲であり、**本書が先回りして書き換えると手順5との境界が崩れる**。
>
> **ただし放置もしない**: `datetime.utcnow()` は Python 3.12 以降で `DeprecationWarning` を出す。**本番だけ直してテストに残すと「置換した」という記録と実態が食い違う**。手順5で同時に置換する（`datetime.now(timezone.utc) - timedelta(hours=1)`。`exp` は数値化されるため**テストの意味は変わらない**）。

### 2-4. `main.py`（変更）

#### 2-4-1. F-21：CORS設定の限定

**設定値を `config.py` の定数に切り出す** 🔧（v0.2で変更・テスト設計書レビューTD-R-01対応）

```python
# config.py（§2-6）
CORS_ALLOW_METHODS = ["GET", "POST", "PUT"]
CORS_ALLOW_HEADERS = ["Authorization", "Content-Type"]
```

```python
# main.py（L33-39 の置換）
from config import CORS_ALLOW_HEADERS, CORS_ALLOW_METHODS

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,             # 変更なし（環境変数）
    allow_credentials=True,             # 変更なし
    allow_methods=CORS_ALLOW_METHODS,   # ["*"] から変更（L37）
    allow_headers=CORS_ALLOW_HEADERS,   # ["*"] から変更（L38）
)
```

#### ⚠️ 定数に切り出す根拠（v0.2追加・テスト設計書レビューTD-R-01対応）

**v0.1 は値を `main.py` に直書きしていた。その場合、F-21 の回帰テストが機能しない。**

テスト設計書 T-P3-05 は `main.py` と**同じ設定を持つフィクスチャ**（`cors_client`）を組んでプリフライトを検証する設計だった。しかしこれは「**テスト側に書いた値と、テスト側に書いた値を比べる**」形になる。

| 状態 | TC-05-3（`PUT` が許可されるか）の結果 |
|---|---|
| `main.py` が `["GET","POST"]`・フィクスチャが `["GET","POST","PUT"]` | **通ってしまう** |

**これは DD-01（本節が是正した欠陥）そのものの構図である。** 「設計書の値と実際の使用が食い違う」ことを検出するための回帰テストが、**本番の値を読まない**なら意味がない。

| 案 | 内容 | 採否 |
|---|---|---|
| **案A** | **`config.py` の定数に切り出し、`main.py` とフィクスチャの双方が同じ定数を読む** | ✅**採用** |
| 案B | フィクスチャを `main.py` の `app` を import して作る | ❌不採用（下記） |
| 案C | 案Aと案Bの併用 | ⏭️要望1採用後に再検討（**§6 #14**） 🔧（v0.3で参照を訂正・レビューDD2-02対応） |

**採用根拠**

| # | 理由 |
|---|---|
| 1 | **乖離が原理的に起きない**。両者が同じ定数を読むため、片方だけ変えることができない |
| 2 | §2-6 は既に `LOGIN_RATE_LIMIT`・`METRICS_WINDOW_DAYS` を `config.py` に置いている。**方針が一貫する** |
| 3 | **要望1の採否に依存しない**。案Bは `TestClient` の context 進入で `startup_event()` が走るため **`ENABLE_SCHEDULER=false` が必要**だが、その分岐は要望1採用時にのみ適用される（§2-4-3・§3）。**採否が決まるまで案Bは使えない** |
| 4 | `config.py` はカバレッジ除外のままでよい（定数定義のため。テスト設計書§1-2-2） |

> **⚠️ 本変更はテスト設計側の都合で本番コードの構造を決めている。** 通常は避けるべきだが、本件は「**テストが本番の値を読めるようにする**」ための最小の変更であり、`config.py` に定数を置くという既存方針の範囲内に収まる。**テストのために本番に余計な分岐や公開範囲の拡大を持ち込むもの（§1-7-3 の `MainView` の export）とは性質が異なる。**

**値の決定**

| 項目 | 変更前 | 変更後 |
|---|---|---|
| `allow_methods` | `["*"]` | **`["GET", "POST", "PUT"]`** |
| `allow_headers` | `["*"]` | **`["Authorization", "Content-Type"]`** |
| `allow_origins` | 環境変数（変更なし） | 変更なし |

> **`PUT` を含める根拠**: `useNews.js` L63・L77 が **`PUT /api/settings`** を呼ぶ。CORS のプリフライトで `PUT` が許可されないと、**ネタバレ防止トグルとチームフィルタが動かなくなる**。F-21 の目的は「`*` をやめて使用するメソッドに限定する」ことであり、**実際に使用しているメソッドを落とすことではない**。
>
> **基本設計書 v0.7 で是正済み**（DD-01。§6 #3）。

| 確認したメソッド | 使用箇所 |
|---|---|
| `GET` | `/api/news`・`/api/status`・`/api/schedule`・`/api/settings` |
| `POST` | `/api/auth/login`・`/api/fetch` |
| **`PUT`** | **`/api/settings`**（`useNews.js` L62-69・L75-84） |
| `DELETE` / `PATCH` | **使用なし** → 許可しない |

| 確認したヘッダ | 使用箇所 |
|---|---|
| `Authorization` | 全認証エンドポイント（`Bearer` トークン） |
| `Content-Type` | `POST /api/auth/login`・`PUT /api/settings`（`application/json`） |
| その他 | **使用なし** → 許可しない |

#### 2-4-2. F-17の前提：`forwarded_allow_ips`（§8 #10）

```python
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
        reload=False,
        proxy_headers=True,                 # 追加
        forwarded_allow_ips="*",            # 追加（基本設計書§4-1）
    )
```

| 項目 | 設計 | 根拠 |
|---|---|---|
| 追加箇所 | `uvicorn.run()`（現行 L68-73） | 基本設計書§4-1 |
| 効果 | `slowapi` の `get_remote_address` が **`X-Forwarded-For` の値を返す** | 既定（`127.0.0.1`）ではプロキシIPが返り、**レート制限が全アクセス共通の1バケットになる** |
| 前提 | **Render以外から直接ポートに到達できないこと** | 同上。ホスティング構成が変わったら再検討する |
| ローカル開発 | **影響なし** | `X-Forwarded-For` が付かないため `request.client.host` がそのまま使われる |

> **`slowapi` の導入（#3）と一体で行う**（計画書 手順4）。`forwarded_allow_ips` だけ入れても効果はなく、`slowapi` だけ入れると**制限が意図どおり働かない**。

#### 2-4-3. `ENABLE_SCHEDULER` による分岐（要望1採用時に有効化・§3-4）

**実装は本節で確定し、変更の適用は§3（採否確定後）とする。**

```python
@app.on_event("startup")
def startup_event() -> None:
    init_db()
    logger.info("DB initialized")
    init_user(crud)
    logger.info("Initial user check completed")
    if ENABLE_SCHEDULER:                       # 追加
        scheduler.start()
        logger.info("Scheduler started")
        check_and_run_batch()                  # ← 分岐対象に含める（基本設計書§5-3）
    else:
        logger.info("Scheduler disabled (ENABLE_SCHEDULER=false)")


@app.on_event("shutdown")
def shutdown_event() -> None:
    if ENABLE_SCHEDULER:                       # 追加：起動していないものは止められない
        scheduler.shutdown()
        logger.info("Scheduler stopped")
```

| 項目 | 設計 | 根拠 |
|---|---|---|
| 分岐対象 | **`scheduler.start()` と `check_and_run_batch()` の両方** | 基本設計書§5-3（v0.2でstartupのバッチ実行を追加） |
| **shutdown も分岐する** 🆕 | `scheduler.shutdown()` も `if` の中 | **起動していないスケジューラに `shutdown()` を呼ぶと `SchedulerNotRunningError` を送出する**（APScheduler）。基本設計書は startup のみに言及しており、**shutdown 側が漏れていた** |
| `init_db()` / `init_user()` | **分岐しない**（常に実行） | 基本設計書§5-3「startup の他の処理の扱い」：いずれも冪等 |
| 既定値 | **`true`**（未設定なら現行動作） | 基本設計書§5-3 |

> **⚠️ shutdown 側の漏れ（DD-02）**: 基本設計書 v0.6 §5-3 は「`scheduler.start()` と startup の `check_and_run_batch()` の両方」を分岐対象としており、**`shutdown_event()` の `scheduler.shutdown()`（`main.py` L63）に触れていなかった**。`ENABLE_SCHEDULER=false` で起動したプロセスを停止すると、**シャットダウン時に `SchedulerNotRunningError` が出る**。本書で分岐対象に加え、**基本設計書 v0.7 で是正済み**（§6 #3）。回帰テストはテスト設計書 TC-16-5（**要望1採用時のみ**）。

### 2-5. `processor/claude_client.py`（変更・F-16）

`USER_PROMPT_TEMPLATE`（L19-42）の末尾に**固有名詞の対訳表**を追加する。

```python
GLOSSARY = """
【固有名詞の表記ルール】
以下の表にある語は、必ず「日本語表記」の列の表記に従うこと。
表にない選手名は、一般的なカタカナ表記を用いること。

| 英語 | 日本語表記 |
|---|---|
| DeRozan | デローザン |
| Valanciunas | バランチューナス |
| Tyler Herro | タイラー・ヒーロー |
| Victor Wembanyama | ヴィクター・ウェンバンヤマ |
| Kel'el Ware | ケレル・ウェア |
| Maluach | マルアチ |
| Giannis | ヤニス |
| Matisse Thybulle | マティス・サイブル |
| Apron | エプロン |
|（以下、主要選手20〜30名を追加）| |
"""

USER_PROMPT_TEMPLATE = """...（現行のまま）...
- JSON 以外の文字列を出力しないこと
""" + GLOSSARY
```

| 項目 | 設計 | 根拠 |
|---|---|---|
| 実装位置 | **`USER_PROMPT_TEMPLATE` の末尾**（`SYSTEM_PROMPT` ではない） | `SYSTEM_PROMPT` は「JSONのみで回答」という**出力形式の指示**に限定されている。役割を混ぜない |
| 定数の分離 | **`GLOSSARY` として独立させる** | 表記の追加・修正が**プロンプト本体に触れずに行える**。改善バックログとして継続的に更新される性質のため |
| 収録範囲 | 要件定義書§3-4-2 の**9件＋主要選手20〜30名** | 基本設計書§4-6 |
| 指示文 | 「**表にある語は必ず表の表記に従う。表にない選手名は一般的なカタカナ表記を用いる**」 | 同上 |
| `{}` のエスケープ | **`GLOSSARY` に `{` `}` を含めない** | `USER_PROMPT_TEMPLATE.format()`（L57）で `KeyError` になる。上記の表形式なら問題ない |

> **⚠️ 手順7での注意**: `GLOSSARY` に波括弧を含む文字列（例：JSON例）を書くと、`.format()` が**実行時に `KeyError` を投げる**。追加時は `{{` `}}` にエスケープするか、波括弧を使わない。
>
> **コスト影響**: 入力トークンが約200〜400トークン増える（1記事あたり）。週50件で月あたり数円未満。要件定義書§3-4-3 の「移行後の無料枠の中で成立するか」は**満たす**（Claude API はフェーズ2実績で月 $1.27〜$1.72）。
>
> **合否の扱い**: 本要件は**改善バックログ項目**であり、未達でもリリースを妨げない（要件定義書§3-4-3）。

### 2-6. `config.py`（追加定数）

```python
# レートリミット設定（F-17）
LOGIN_RATE_LIMIT = "5/minute"

# CORS設定（F-21）🆕 v0.2：main.py とテストフィクスチャの双方がここを読む（§2-4-1）
CORS_ALLOW_METHODS = ["GET", "POST", "PUT"]
CORS_ALLOW_HEADERS = ["Authorization", "Content-Type"]

# 運用指標（改修要件5a）
METRICS_WINDOW_DAYS = 7        # /api/status の metrics の集計期間

# スケジューラ有効化（要望1採用時に false を設定する）
ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "true").lower() != "false"
```

| 定数 | 値 | 根拠 |
|---|---|---|
| `LOGIN_RATE_LIMIT` | `"5/minute"` | 基本設計書§4-1 |
| **`CORS_ALLOW_METHODS`** 🆕 | `["GET", "POST", "PUT"]` | 基本設計書§4-5（v0.7）。**定数にする理由は§2-4-1**（テストが本番の値を読めるようにする） |
| **`CORS_ALLOW_HEADERS`** 🆕 | `["Authorization", "Content-Type"]` | 同上 |
| `METRICS_WINDOW_DAYS` | `7` | 基本設計書§6-1（N=7日） |
| `ENABLE_SCHEDULER` | 既定 `True` | 基本設計書§5-3。**未設定なら現行動作を維持** |

> **`ENABLE_SCHEDULER` の判定を `!= "false"` にする根拠**: `== "true"` だと `"True"`・`"1"`・`"yes"` がすべて `False` になる。**「明示的に false と書いたときだけ無効」**とし、**既定値が意図せず反転しない**形にする。`.lower()` により `"False"`・`"FALSE"` も拾う。
>
> **必須チェックは追加しない**。`ENABLE_SCHEDULER` は未設定でも動く（既定 true）。

### 2-7. `requirements.txt`（追加）

```
slowapi
```

| 条件 | 追加するもの | 根拠 |
|---|---|---|
| **採否非依存** | **`slowapi`**（F-17・§8 #3） | §2-1-1 |
| **要望1採用時** 🆕（v0.2・レビューDD-R-02対応） | **`psycopg[binary]`** | §3-4。**移行時に併せて追加する** |

| 項目 | 内容 |
|---|---|
| バージョン固定 | **しない**（既存の記述方針に揃える。`bcrypt<4.0.0` のような制約が必要になった場合のみ付ける） |
| 依存 | `slowapi` は `limits` に依存する。`redis` は**任意依存**であり、既定のインメモリストレージでは不要 |
| **`sqlalchemy` の版** ⚠️ | **2.0系から下げない**。§3-4 で `connect_args={"check_same_thread": False}` を削除できるのは、**SQLAlchemy 2.0 が file-based SQLite に対してこれを自動付与するため**である。1.x に戻すと前提が変わる |

> **⚠️ v0.1 は「`slowapi` **のみ**」と断定していた**（レビューDD-R-02）。§3-4 が `psycopg[binary]` の追加を指示しているにもかかわらず、§2-7 が「requirements.txt に何を足すか」を扱う唯一の節として閉じていたため、**§3 を読まずに §2 だけで実装すると取りこぼす**。§3-3 の `batch.yml` は `pip install -r requirements.txt` の後に Neon へ接続するため、**GitHub Actions のバッチが初回実行時に接続エラーで落ちる**。
>
> **要望1の採否確定は手順6であり、§2 と §3 の実装時期が離れることが確定している**点も効く。条件欄を設けて1つの表にまとめる。

> **インメモリストレージで足りる根拠**: 本アプリのAPIプロセスは**1インスタンス**である（Render無料プランは複数インスタンスにならない）。プロセスが再起動するとカウンタは消えるが、**ブルートフォース対策としては再起動のたびに5回試せるだけ**であり、実効性を損なわない。

---

## 3. 差分設計（要望1採用時）

> **§3-2 を除き、本節の実装は要望1の採否確定（手順6）後に着手する**（§0-3）。本書では**設計を確定させる**。

### 3-1. `backend/run_batch_once.py`（新規）

```python
"""GitHub Actions から起動する1回限りのバッチ実行スクリプト。
APScheduler を介さず、run_batch() と run_game_schedule_batch() を直接呼ぶ。
"""
import logging
import os
import sys

import requests

from db import crud
from db.models import init_db
from scheduler import run_batch, run_game_schedule_batch

logger = logging.getLogger(__name__)


def main() -> int:
    # ① スキーマの用意（基本設計書§5-2：移行手順4のために必須。冪等）
    init_db()

    # ② 記事取得
    run_batch()

    # ③ 試合日程取得
    run_game_schedule_batch()

    # ④ 成否判定（基本設計書§5-2 案A・§8 #13）
    log = crud.get_latest_fetch_log()
    if log is None or log["error_message"] is not None:
        logger.error("batch failed: %s", log["error_message"] if log else "no fetch_log")
        return 1                      # ← ping せず非ゼロ終了

    # ⑤ ping（判定に合格した場合のみ。基本設計書§6-2-2）
    url = os.getenv("HEALTHCHECK_PING_URL")
    if url:
        try:
            requests.get(url, timeout=10)
        except Exception as exc:
            logger.warning("healthcheck ping failed: %s", exc)   # pingの失敗で落とさない
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

| 項目 | 設計 | 根拠 |
|---|---|---|
| 呼ぶ関数 | `init_db()` → `run_batch()` → `run_game_schedule_batch()` | 基本設計書§5-2。**`check_and_run_*` は呼ばない**（4時間ゲートを外す） |
| **`init_user()` は呼ばない** | — | 基本設計書§5-2。バッチは認証を使わない。§3-2の目的が崩れる |
| **成否判定の位置** 🆕 | **③の後・⑤の前**（`run_game_schedule_batch()` の後） | 判定に使う `fetch_log` は②で書かれる。③の後に置いても値は変わらないが、**「全部走らせてから判定する」方が読み手に意図が伝わる** |
| **判定の実装** | **`crud.get_latest_fetch_log()`（`db/crud.py` L97）を使う** | 基本設計書§5-2（v0.6で確定）。`/api/status`（`routes.py` L95）で既に使われている |
| **`log is None` の扱い** 🆕 | **失敗とみなす（`return 1`）** | `run_batch()` は成功・失敗いずれでも `save_fetch_log()` を呼ぶ（`scheduler.py` L63・L171）。**`None` はバッチが `save_fetch_log()` に到達しなかったことを意味する**（例外は送出されないが異常） |
| **終了コード** | 正常 `0`／異常 `1`。`sys.exit(main())` | GitHub Actions は**非ゼロ終了でジョブ失敗**とし、標準機能のメール通知が飛ぶ |
| 例外の扱い | **握りつぶさない**（`try/except` で囲まない） | DB障害（#4）は例外として送出され、非ゼロ終了になる。§4-1参照 |
| ping の失敗 | **`warning` ログのみ・終了コードに影響させない** | 監視の ping が落ちてもバッチは成功している。**pingの失敗でジョブを失敗にすると、原因の切り分けができなくなる** |
| ping URL 未設定 | **スキップ**（`config.py` の必須チェックに加えない） | 基本設計書§6-2-2。バッチの目的に必須ではない |
| 設定する環境 | **GitHub Actions 上でのみ**。ローカルでは設定しない | 同上（ローカル実行のpingが本番の停止を隠す） |

> **⚠️ `HEALTHCHECK_PING_URL` を `config.py` ではなく `os.getenv()` で直接読む根拠**: この値は**このスクリプトでしか使わない**。`config.py` に置くと、`config` を import する全モジュール（`scheduler.py` 等）が知る必要のない設定を抱えることになる。§3-2 の「用途別に分離する」方針と一貫させる。
>
> **監視サービスの選定（§8 #11）は手順6の後**である。本書が確定するのは**呼び出しの位置と条件**のみであり、**URLの形式・サービス名には依存していない**（`GET` 1回で ping できるサービスであればよい）。

#### 3-1-1. 失敗4種と本スクリプトの挙動（基本設計書§5-2の表の実装対応）

| # | 失敗 | 実装上の経路 | 終了コード | ping |
|---|---|---|---|---|
| 1 | RSS全ソース失敗 | `run_batch()` が `error_message` 付きで `save_fetch_log()` → ④で検知 | **1** | ❌しない |
| 2 | 試合日程取得の失敗 | `run_game_schedule_batch()` が例外を握りつぶす → **検知できない** | 0 | ✅する |
| 3 | Claude API の RateLimit | `error_message` は NULL のまま → **検知できない** | 0 | ✅する |
| 4 | DB接続失敗 | `init_db()` / `crud` が例外を送出 → **未捕捉のまま伝播** | **1**（Python既定） | ❌しない |

> **#2・#3 が対象外であることは基本設計書§5-2で確定済み**である。#2 は意図的除外、#3 は週次チェックリストで確認する（`api_limit_exceeded`）。**本書で扱いを変えない。**
>
> **#3 の影響**: 上限超過中は**記事が保存されない**（`scheduler.py` L112-123）。当該期間の記事は失われる。発生見込みが低いことを根拠に週次確認に委ねている（基本設計書§5-2）。

### 3-2. `config.py` の必須チェックの用途別分離（**要望1の採否に依存しない**）

基本設計書§5-5（案A）を実装に落とす。**先-1（2026年9月まで）に実施する**（§8 #8）。

#### 3-2-1. `config.py`（変更）

```python
# APIキー（共通・バッチもAPIも使う）
ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
BALLDONTLIE_API_KEY = os.getenv("BALLDONTLIE_API_KEY", "")
if not ANTHROPIC_API_KEY or not BALLDONTLIE_API_KEY:            # 追加（先-1）
    raise RuntimeError(
        "ANTHROPIC_API_KEY / BALLDONTLIE_API_KEY が未設定です。環境変数に設定してください。"
    )

# JWT設定
SECRET_KEY = os.getenv("SECRET_KEY", "")
# ↓ L61-64 の必須チェックを削除し auth/jwt.py へ移す
JWT_ALGORITHM            = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

# ユーザー設定（起動時initスクリプト用）
INIT_USERNAME      = os.getenv("USERNAME", "")
INIT_USER_PASSWORD = os.getenv("USER_PASSWORD", "")
# ↓ L71-74 の必須チェックを削除し auth/users.py へ移す
```

#### 3-2-2. `auth/jwt.py`（追加）

```python
from config import ACCESS_TOKEN_EXPIRE_DAYS, JWT_ALGORITHM, SECRET_KEY

if not SECRET_KEY:                                              # 追加（config.py から移設）
    raise RuntimeError(
        "SECRET_KEY が未設定です。openssl rand -hex 32 で生成し環境変数に設定してください。"
    )
```

#### 3-2-3. `auth/users.py`（追加）

```python
from config import INIT_USER_PASSWORD, INIT_USERNAME

if not INIT_USERNAME or not INIT_USER_PASSWORD:                 # 追加（config.py から移設）
    raise RuntimeError(
        "USERNAME / USER_PASSWORD が未設定です。環境変数に設定してください。"
    )
```

| 区分 | 検証タイミング | 対象 |
|---|---|---|
| **共通** | `config.py` のロード時 | `ANTHROPIC_API_KEY`・`BALLDONTLIE_API_KEY`（**先-1で追加**） |
| **認証系** | `auth/jwt.py`・`auth/users.py` のロード時 | `SECRET_KEY`／`INIT_USERNAME`・`INIT_USER_PASSWORD` |

> **効果**: `scheduler.py` は `auth` を import しない。したがって `run_batch_once.py`（→ `scheduler` → `config`）の経路では**認証系シークレットが要求されない**。要望1採用時、**GitHub Secrets に登録するのはAPIキー2件と `DATABASE_URL` だけで済む**。
>
> **値そのものは扱わない**。本書に実際のキー・パスワードは記載しない。設定はTakumi様が各環境の管理画面で行う。
>
> **`conftest.py` への影響なし**（基本設計書§5-5）: L19-23 は5件すべてにダミー値を `os.environ.setdefault` しており、**移設後も全チェックを通過する**。余分に設定していても害はない。
>
> **⚠️ import 順序の注意**: `auth/jwt.py` のチェックは**モジュールのロード時**に走る。`main.py` は L9 で `auth.users` を、`api/routes.py` は L5-6 で `auth.jwt`・`auth.users` を import しているため、**API起動時には従来どおり全件が検証される**。緩和されるのは**バッチ経路だけ**である。

### 3-3. `.github/workflows/batch.yml`（新規）

```yaml
name: NBA News Batch

on:
  schedule:
    - cron: '0 21,1,5,9,13,17 * * *'    # UTC → JST 6/10/14/18/22/2時
  workflow_dispatch:                    # 手動実行（/api/fetch の代替）

jobs:
  run-batch:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: pip
      - run: pip install -r app/backend/requirements.txt
      - name: Run batch
        working-directory: app/backend
        env:
          ANTHROPIC_API_KEY:    ${{ secrets.ANTHROPIC_API_KEY }}
          BALLDONTLIE_API_KEY:  ${{ secrets.BALLDONTLIE_API_KEY }}
          DATABASE_URL:         ${{ secrets.DATABASE_URL }}
          HEALTHCHECK_PING_URL: ${{ secrets.HEALTHCHECK_PING_URL }}
        run: python run_batch_once.py
```

| 項目 | 設計 | 根拠 |
|---|---|---|
| cron式 | **`0 21,1,5,9,13,17 * * *`（UTC）** | 基本設計書§5-7。JST 6/10/14/18/22/2時 |
| 手動実行 | **`workflow_dispatch`** | 基本設計書§5-4：`/api/fetch` の代替 |
| `working-directory` | **`app/backend`** | 相対 import（`from db import crud`）と `logs/` の作成位置を現行と揃える |
| タイムアウト | **20分** | 通常は数分。無限に回って無料枠（月2000分）を消費しないための上限 |
| Secrets | **認証系（`SECRET_KEY`・`USERNAME`・`USER_PASSWORD`）を渡さない** | §3-2 の目的。バッチ経路では要求されない |
| `concurrency` | **設定しない** | 4時間間隔に対し実行は数分。重複起動は起きない |

> **⚠️ `logs/` ディレクトリ**: `main.py` L15 の `os.makedirs("logs", exist_ok=True)` は**`main.py` にしかない**。`run_batch_once.py` は `main.py` を import しないため、`logging.FileHandler("logs/...")` を設定するなら**同等の行が必要**になる。本書では **`run_batch_once.py` はファイル出力を設定せず、標準出力のみ**とする（GitHub Actions のログに残るため、ファイルに書く必要がない）。
>
> **cron の遅延について**: GitHub Actions の scheduled workflow は**混雑時に数分〜十数分遅れる**。基本設計書§6-2-2 の猶予1時間はこれを吸収する設計である。
>
> **60日無活動での自動無効化**（リスク調査書§1-5 リスク2）は本ファイルでは防げない。外部cron監視（§8 #11・手順6の後）で検知する。

### 3-4. `db/models.py`（変更・Neon移行）

```python
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///nba_news.db")
engine = create_engine(DB_PATH, pool_pre_ping=True)
```

| 項目 | 変更前（L82-83） | 変更後 |
|---|---|---|
| `DATABASE_URL` の意味 | **ファイルパス**（`sqlite:///` を後から付けていた） | **接続URL全体**（`postgresql+psycopg://...` または `sqlite:///...`） |
| `connect_args` | `{"check_same_thread": False}` | **削除**（SQLite専用のオプション） |
| 接続の健全性 | なし | **`pool_pre_ping=True`** を追加 |

| 論点 | 設計 | 根拠 |
|---|---|---|
| **`DATABASE_URL` の意味が変わる** | 移行手順（リスク調査書§1-4-9）で**環境変数の値も同時に差し替える**必要がある | 現行は `nba_news.db` のような**パス**が入る。URLに変えないと `create_engine` が失敗する |
| 既定値 | **`"sqlite:///nba_news.db"`** | 未設定時にローカルSQLiteで動く現行の挙動を維持する |
| `connect_args` の削除 | **PostgreSQLでは `check_same_thread` が未知の引数**でエラーになる | — |
| `pool_pre_ping` | **Neonは無操作でコンピュートが休止する**。切れた接続を掴むと最初のクエリが失敗する | リスク調査書§1-4 |
| ドライバ | **`psycopg[binary]`** を `requirements.txt` に追加 | 現行に Postgres ドライバはない |
| ORM側の変更 | **なし** | `crud.py` は全関数がSQLAlchemy ORM（生SQL 0件） |

> **⚠️ 日時比較が文字列比較のままである点**: `fetched_at`・`executed_at` は **TEXT カラム**であり、`>= cutoff`（文字列）で比較している（`crud.py` L57・§2-2-1）。**ISO8601 は辞書順と時系列順が一致する**ため、PostgreSQL でも正しく動く。**カラム型を `TIMESTAMP` に変えない**（変えると `crud.py` の全日時処理が影響を受ける）。
>
> **移行の作業順序はリスク調査書§1-4-9（11ステップ）に従う。本書では変更しない**（基本設計書§5-6）。

### 3-5. `/api/fetch` の削除（§8 #4）

| 項目 | 内容 |
|---|---|
| 削除対象 | `api/routes.py` **L104-110**（`trigger_fetch()`）と、L1 の `BackgroundTasks`・L8 の `from scheduler import run_batch` |
| 代替 | **`workflow_dispatch`**（§3-3） |
| **テストの削除対象** 🆕 | `backend/tests/test_routes.py` **L263-267 `test_post_fetch()`**（`/api/fetch` を叩く唯一のテスト）。**L252 のセクションコメント**「`# ── GET /api/status・POST /api/fetch ──`」も同時に修正する |

> **⚠️ L8 の import を消す意味**: `routes.py` が `scheduler` を import しなくなると、**API層がバッチ層に依存しなくなる**。これは§3-2（`config.py` の分離）と同じ方向の整理である。ただし `scheduler` は `main.py` L12 でも import されているため、**API起動時に `scheduler` がロードされること自体は変わらない**。
>
> **実際の削除は採否確定後**（基本設計書§8 注記）。不採用なら `/api/fetch` は残るため、削除してはならない。

---

## 4. エラーハンドリング設計

### 4-1. バックエンド

| 発生源 | 例外 | 扱い | 利用者への応答 |
|---|---|---|---|
| ログイン試行の超過（F-17） | `RateLimitExceeded` | `slowapi` の既定ハンドラ | **HTTP 429** |
| 日付パラメータの不正（F-18） | Pydantic の検証エラー | FastAPI が自動処理 | **HTTP 422** |
| JWT 不正・期限切れ | — | `get_current_user()`（既存 L24-28） | **HTTP 401** |
| `metrics` の集計失敗（§2-2-1） | DB例外 | **握りつぶさない**。`/api/status` 全体が500になる | HTTP 500 |
| `run_batch_once.py` のDB障害 | `OperationalError` 等 | **未捕捉のまま伝播**→非ゼロ終了 | （バッチのため応答なし） |
| ping の失敗（§3-1） | `requests` の例外 | **`warning` ログのみ**。終了コードに影響させない | 同上 |

> **`metrics` を握りつぶさない根拠**: `try/except` で `metrics: null` を返すと、**週次チェックリストで「指標が取れない」ことに気付けない**。`/api/status` は監視の入口であり、**壊れていることが見えるべき**である。既存4項目も同じ扱い（`crud` の例外はそのまま500になる）。

### 4-2. フロントエンド

| 発生源 | 扱い | 利用者への表示 |
|---|---|---|
| `ratio()` に `null` / `undefined`（§1-2） | `?? ''` で吸収。**例外を投げない** | 影響なし（スコア0扱い） |
| `fetched_at` が不正な文字列（§1-3-3） | `Number.isNaN` を判定し `recency = 0` | 関連度が下がるのみ |
| `source_url` が不正（§1-4-4） | `isSafeUrl()` が `false` | **「原文を読む」を描画しない** |
| `score_data` の JSON パース失敗 | 既存 `ScoreDisplay`（L30-42）の `try/catch` で `null` | 既存のまま |
| ログインの 429（F-17） | **`useAuth.login` がステータスコードを載せた例外を投げ、`LoginForm` が分岐する** | 429専用の文言（§4-2-1） |

#### 4-2-1. ⚠️ 429 のハンドリングには `useAuth.js` の変更が必要

**現行はステータスコードがUIに届かない。**

```javascript
// useAuth.js L15（現行）
if (!res.ok) throw new Error('ログインに失敗しました');
```

```javascript
// LoginForm.jsx L11-15（現行）
try { await onLogin(username, password); }
catch { setError('ユーザー名またはパスワードが正しくありません'); }
```

`useAuth.login` は **`!res.ok` を一括して同じ例外**にし、`LoginForm` は `catch` で**固定文言**を出す。したがって F-17 で 429 を返すようにしても、利用者には「**ユーザー名またはパスワードが正しくありません**」と表示される。**正しい認証情報を入力しているのに間違いを疑い続けることになる。**

**設計：例外にステータスコードを載せる**

```javascript
// useAuth.js（変更）
if (!res.ok) {
  const err = new Error('ログインに失敗しました');
  err.status = res.status;              // 追加
  throw err;
}
```

```javascript
// LoginForm.jsx（変更）
try { await onLogin(username, password); }
catch (e) {
  setError(
    e.status === 429
      ? 'ログインの試行が多すぎます。1分ほど待ってから再試行してください。'
      : 'ユーザー名またはパスワードが正しくありません'
  );
}
```

| 論点 | 設計 | 根拠 |
|---|---|---|
| 例外にプロパティを付ける | **`err.status`** | カスタム例外クラスを新設するより軽い。判定箇所は1つ |
| 文言 | **「1分ほど待ってから再試行してください」** | `LOGIN_RATE_LIMIT = "5/minute"` と整合する。**具体的な待ち時間を書く**（「しばらく」だと何分か分からない） |
| その他のステータス | **従来どおり「認証情報が正しくない」** | 500等をわざわざ区別しても利用者にできることは変わらない |
| ネットワークエラー | `fetch` 自体が throw する。`e.status` は `undefined` → 従来の文言 | 変更なし |

> **本節は F-17 の一部である**。基本設計書§4-1 は「超過時 HTTP 429」までを決めたが、**429 が利用者にどう見えるか**は決めていなかった。**サーバが正しく429を返しても、UIが401と同じ文言を出すなら F-17 の目的（ブルートフォース対策）に伴う利用者への説明責任を果たせない。**

---

## 5. 設計自己チェックリスト

> **計画書§8-0-3（自己チェックの二分）に従い、A（機械確認）とB（判断）に分けて実施する。**

### 5-1. A：機械確認（コマンドで実行）

- [x] **参照先ファイル・パスの実在** 🔧（v0.3で一覧を更新・レビューDD2-03対応） → 本書が参照する**既存ファイル17件**（`useNews.js`・`useAuth.js`・`NewsCard.jsx`・`FilterBar.jsx`・`SpoilerOverlay.jsx`・**`App.jsx`**・**`LoginForm.jsx`**・`routes.py`・`crud.py`・`models.py`・`main.py`・`config.py`・`auth/jwt.py`・`auth/users.py`・`claude_client.py`・`dedup.py`・`requirements.txt`）**全件の実在を確認**。**新規作成予定7件**（`levenshtein.js`・`relatedness.js`・**`utils/constants.js`**・`RelatedNews.jsx`・`run_batch_once.py`・`api/limiter.py`・`batch.yml`）の不在は**想定内**
  - **v0.2 の一覧は §1-7 の新設（`App.jsx`・`constants.js`）と §4-2-1（`useAuth.js`・`LoginForm.jsx`）を反映していなかった**。実在の確認自体は照合リスト [40][41][47]〜[50] で済んでいたが、**一覧の記述が古いまま**だった。**DD-R-01 の原因は「基本設計書§1-2 の一覧を出発点にした」ことであり、同じ形の一覧が本書にも残っていた**
- [x] **本文から §6 への番号参照を全件突き合わせる** 🆕（v0.3追加・レビューDD2-02対応） → 本文中の `§6 #N` 参照**12箇所**を §6 の表と突合。**1件がずれていた**（§2-4-1 の案C が `#12` を指していたが、正しくは `#14`。v0.2 で §6 に3行追加した際、本文からの参照を追っていなかった）
- [x] **コード引用の行番号と内容**（**本書が言及する実装箇所を全件照合**）

```
[1]  useNews.js       L21     const [revealedIds, setRevealedIds] = useState(new Set());  ✅一致
[2]  useNews.js       L62-69  toggleSpoilerGuard の PUT /api/settings                     ✅一致
[3]  useNews.js       L75-84  toggleSpursFilter の PUT /api/settings                      ✅一致
[4]  NewsCard.jsx     L56     const needsSpoiler = spoilerGuard && has_score && !isRevealed ✅一致
[5]  NewsCard.jsx     L66-90  二段展開ブロック（SpoilerOverlay / summary_ja）             ✅一致
[6]  NewsCard.jsx     L92-102 MetaRow（source・時刻・原文リンク）                          ✅一致
[7]  NewsCard.jsx     L44-53  formatRelativeTime（published_at に Date.now() の差）        ✅一致
[8]  NewsCard.jsx     L30-42  ScoreDisplay の try/catch                                   ✅一致
[9]  FilterBar.jsx    L14/L24 「全チーム」／「チームのみ」                                  ✅一致
[10] api/routes.py    L82-90  /schedule（start_date: str, end_date: str）                 ✅一致
[11] api/routes.py    L93-101 /status（既存4項目）                                         ✅一致
[12] api/routes.py    L104-110 /fetch（BackgroundTasks で run_batch）                      ✅一致
[13] api/routes.py    L42-51  /auth/login（body: LoginBody・request 引数なし）             ✅一致
[14] api/routes.py    L5-6    from auth.jwt / from auth.users の import                    ✅一致
[15] db/crud.py       L43     Article.is_duplicate == 0 のフィルタ                         ✅一致
[16] db/crud.py       L97     def get_latest_fetch_log() -> dict | None                    ✅一致
[17] db/crud.py       L150    def get_game_schedule(start_date: str, end_date: str)        ✅一致
[18] db/crud.py       L64     .filter(Article.fetched_at >= cutoff)（文字列比較）           ✅一致
[19] db/models.py     L23-24  published_at（nullable）／fetched_at（NOT NULL）             ✅一致
[20] db/models.py     L82-83  DB_PATH / create_engine の connect_args                      ✅一致
[21] main.py          L15     os.makedirs("logs", exist_ok=True)                           ✅一致
[22] main.py          L37-38  allow_methods=["*"] / allow_headers=["*"]                    ✅一致
[23] main.py          L50-58  startup_event（scheduler.start / check_and_run_batch）       ✅一致
[24] main.py          L61-64  shutdown_event（scheduler.shutdown）                          ✅一致
[25] main.py          L68-73  uvicorn.run（forwarded_allow_ips 指定なし）                   ✅一致
[26] main.py          L9/L12  from auth.users / from scheduler の import                   ✅一致
[27] config.py        L59-64  SECRET_KEY の必須チェック                                     ✅一致
[28] config.py        L68-74  INIT_USERNAME / INIT_USER_PASSWORD の必須チェック             ✅一致
[29] config.py        L7-8    ANTHROPIC_API_KEY / BALLDONTLIE_API_KEY（チェックなし）       ✅一致
[30] auth/jwt.py      L11     datetime.utcnow() + timedelta(...)                           ✅一致
[31] auth/jwt.py      L19     jwt.decode（exp の数値比較）                                  ✅一致
[32] auth/users.py    L3      from config import INIT_USER_PASSWORD, INIT_USERNAME         ✅一致
[33] claude_client.py L19-42  USER_PROMPT_TEMPLATE                                        ✅一致
[34] claude_client.py L57     USER_PROMPT_TEMPLATE.format(...)                            ✅一致
[35] processor/dedup.py L24   ratio(new_title.lower(), existing_title.lower())            ✅一致
[36] scheduler.py     L63・L171 save_fetch_log() の呼び出し（成功・失敗の両方）             ✅一致
[37] scheduler.py     L112-123 ⑤ Claude API処理（上限超過中は保存せず continue）           ✅一致
[38] tests/conftest.py L19-23 os.environ.setdefault ×5                                    ✅一致
[39] requirements.txt        python-Levenshtein あり／slowapi・Postgresドライバなし        ✅一致
[40] useAuth.js       L15     if (!res.ok) throw new Error('ログインに失敗しました')        ✅一致
[41] LoginForm.jsx    L11-15  try/catch で固定文言を表示（ステータスコードを見ない）        ✅一致
[42] tests/test_routes.py L263-267  test_post_fetch（/api/fetch の唯一のテスト）           ✅一致
[43] tests/test_routes.py L119  datetime.utcnow() - timedelta(hours=1)  ← ⚠️置換漏れ候補    ✅一致
[44] db/crud.py       L3      from sqlalchemy import desc（func なし）← v0.2               ✅一致
[45] db/crud.py       L5      from config import DATA_RETENTION_DAYS（他なし）← v0.2        ✅一致
[46] db/crud.py       L6      from .models import ... FetchLog ...（既に import 済み）← v0.2 ✅一致
[47] App.jsx          L2/L7   import { useNews } / import { NewsCard }  ← v0.2             ✅一致
[48] App.jsx          L38-51  useNews() の分割代入（既存12件）  ← v0.2                      ✅一致
[49] App.jsx          L87-96  articles.map(...) → <NewsCard ...>（props 5件）  ← v0.2       ✅一致
[50] App.jsx          L27-35 / L37  App は export default・MainView は非export  ← v0.2      ✅一致
[51] api/routes.py    L1      from fastapi import ...（**Request を含まない**）← v0.3        ✅一致
```

**不一致：0件**

> **[43] は本書の記述を1件変更させた**。§2-3 は当初「本番コードの `utcnow()` は `auth/jwt.py` L11 のみ」と書いていたが、A区分の全文検索で **`tests/test_routes.py` L119 にも残存**していることが分かった。§2-3 と§6 #11 に反映した。**機械確認が本文を確定させた例**（計画書§8-0-3 B区分）。
>
> **[44]〜[46] は v0.2 で追加した**（レビューDD-R-04）。**本書が「import を追加せよ」と書いている以上、その行は照合対象である**。v0.1 は照合リストに入れておらず、「`FetchLog` を追加」（既存のため不要）・「`METRICS_WINDOW_DAYS` の追加指示なし」（必要なのに欠落）という2つの誤りを検出できなかった。**指示の対象になっている行は、引用していなくても照合する。**
>
> **[47]〜[50] は v0.2 で追加した**（レビューDD-R-01）。`App.jsx` は v0.1 では言及自体がなかったため照合対象にもなっていなかった。**§1-7 の新設に伴い照合対象に加えた。**

- [x] **採番の一意性・昇順** → §0-2（基本設計書§8の13件）・§5-1の照合リスト・§6 いずれも**連続・重複なし**
- [x] **上位文書の項目の消化** → 要件定義書§1-2 の F-13〜F-21 **全件に実装仕様あり**（§5-3の対応表で確認）。基本設計書§8 の13件を§0-2で全件追跡
- [x] **数値の再現** → §1-2-3 の照合用数値例6件を**式に代入して再計算し一致**を確認。§1-3-1 の重み合計 `0.2+0.6+0.2 = 1.0`

### 5-2. B：判断

- [x] **基本設計書の決定を変更していないか** → 方式・閾値・採否はすべて基本設計書のまま。**変更が必要と判断した2件は§6 #3 に「基本設計書の是正」として記録**し、本書だけで書き換えていない
- [x] **呼び出し先の関数が失敗時にどう振る舞うか**（計画書§8-0-3 B区分） → `run_batch()`（早期リターン）・`run_game_schedule_batch()`（try/except）・`get_latest_fetch_log()`（`None` を返しうる）を確認し、**`log is None` を失敗として扱う**設計にした（§3-1）
- [x] **失敗時にデータがどうなるか**（同・v2.2追記） → #3（RateLimit）は**記事が保存されない**ことを§3-1-1に明記。設計を変えないが、**実装者が「翻訳だけ止まる」と誤解しない**形にした
- [x] **設計値が実環境で意図どおり働くか** → `forwarded_allow_ips`（§2-4-2）・`.isoformat()`（§2-1-2）・`fetched_at` のJSパース（§1-3-2）・`allow_methods` と `PUT`（§2-4-1）・`scheduler.shutdown()`（§2-4-3）を**実装を読んで確認**
- [x] **既存の構造を壊していないか** → `revealedIds`・`SpoilerOverlay`・`needsSpoiler`（L56）・`crud.get_game_schedule()` のシグネチャ・`/api/status` の既存4項目を**いずれも変更しない**
- [x] **要望1の採否に依存する箇所と依存しない箇所を分けているか** → §0-3で所在を明示。**§3-2 だけが§3にありながら採否非依存**であることを明記
- [x] **「後工程で決める」とした事項が、本当に後工程でよいか** → §0-2の⏭️6件を検証。**#9・#12（手順5）は本書で関数境界と数値例を提示**し、テスト設計が仕様を推測しなくて済む形にした
- [x] **新しい仕組みを導入したとき、既存実装との噛み合わせを確認したか** → `slowapi` が **`request: Request` 引数を要求する**こと（§2-1-1）、`limiter` の**循環importを避ける配置**（`api/limiter.py`）を確認
- [x] **対処を決めたとき、その適用範囲を書いたか** → §3-1-1で**#1・#4のみ検知でき、#2・#3は対象外**であることを実装対応表として再掲
- [x] **機械確認の結果が本文の未確定事項を解消していないか**（計画書§8-0-3・v2.2追記） → **3件で本文が変わった**：[30][31] により **§8 #2（naive/aware）を「影響なし」と確定**（§2-3）／[22] により `allow_methods` と `PUT` の不整合を検出（§2-4-1）／**[43] により `tests/test_routes.py` L119 の `utcnow()` 残存を検出**し§2-3・§6 #11 を追加。[40][41] により **429 の分岐には `useAuth.js` の変更が要る**ことが判明し§4-2-1を新設
- [x] **状態を変える処理が運用を壊さないか** → `toggleExpand` の副作用（`relatedExpandedIds` 削除・`resetSpoiler`）が**冪等**であることを確認し、StrictMode の二重実行に耐えることを明記（§1-1-2）
- [x] **例示コードの内部整合** → §1-1-2 の `toggleExpand` / `toggleRelatedExpand` が§1-1-1の型（`Set` / `Map<number,Set<number>>`）と一致。§1-5 の props が§1-4-1の props と一致。**§1-4-2 の `<RelatedNews>` を実際の props に展開**し（v0.2）、§1-5 の受け口と1対1で対応することを確認
- [x] **一覧表に載っていない実ファイルがないか（実体→宣言の逆方向）** 🆕（v0.2追加・レビューDD-R-01対応） → `grep -rn "NewsCard\|useNews" frontend/src/` で呼び出し元を洗い、**`App.jsx` が基本設計書§1-2 のコンポーネント一覧11件に無い**ことを検出。§1-7 を新設し、**DD-03 として基本設計書への是正を引き継いだ**（§6 #12）。**戻り値や props を増やす設計では、値を受け渡す中間の呼び出し元が一覧から落ちやすい**
- [x] **nullable が生まれる場所と、それを潰す場所の両方を書いたか** 🆕（v0.2追加・レビューDD-R-01 問題2対応） → `relatedExpandedIds.get()` が **`undefined` を返すのは通常状態**（§1-1-2 が空 `Set` のときエントリを削除するため）。**渡す側（§1-7）と受ける側（§1-5）の両方**に既定値を置いた。v0.1 は型を `Set<number> | undefined` と**明示的に nullable と宣言しながら、潰す場所を書いていなかった**
- [x] **例示コードと、それを説明する注記・表が一致しているか** 🆕（v0.3追加・レビューDD2-01対応） → §2-1-1 の注記が「`limiter` は `api/limiter.py` に置き両方がそこから import する」としているのに、**直上のコードブロックは `limiter = Limiter(...)` を独自に生成していた**。**実装者はコードブロックを先に読む**ため、注記が正しくても救いにならない。全コードブロックを直前・直後の注記と突合し直した
- [x] **表・コードブロックを足したあと、それを指す記述と、置き換わった元の記述を追ったか** 🔧（v0.3新設・**v0.4で対象を「表」から「表・コードブロック」に拡張**・レビューDD3-01対応） → v0.2 は §6 に3行（#12〜#14）を足したが**§2-4-1 の番号参照が #12 のまま**だった。§1-7 を新設したが**§5-1 の参照先ファイル一覧に反映していなかった**。
  - **v0.3 で同型がもう1件出た**: §2-1-1 の冒頭に `api/limiter.py` のコードブロックを**新設したが、節の後半にあった同内容のブロックを消していなかった**。同一内容が2箇所にあると**片方だけ更新したときに乖離する**——これは本書§2-4-1 が扱った問題（`main.py` とフィクスチャの2箇所に同じ値を書くと食い違う）と**同じ型**である。`config.py` の定数に切り出したのと同じ理由で、**設計書の中でも同じ内容を2箇所に置かない**。
  - **v0.4 で対象を「表・コードブロック」に広げた**。行を足す／ブロックを足すのいずれも、**足したあとに「それを指す記述」と「置き換わった元の記述」の両方を追う**。
  - **確認方法**: コードブロックを機械抽出してから当てる（`grep -n '^\`\`\`'`）。**思いついた順に読むと、同じ内容の2つ目を読み飛ばす。**
- [x] **指示の対象になっている行を照合したか（引用していなくても）** 🆕（v0.2追加・レビューDD-R-04対応） → §2-2-1 が「import を追加せよ」と書く `crud.py` L1-6 を照合リストに追加（[44]〜[46]）。**「`FetchLog` を追加」は既に import 済みで不要、`METRICS_WINDOW_DAYS` は必要なのに欠落**という2つの誤りを検出

### 5-3. 要件の消化（F-13〜F-21）

| ID | 要件 | 実装仕様 | 状態 |
|---|---|---|---|
| F-13 | ニュース本文の展開表示 | §1-1・§1-4・**§1-7** | ✅ |
| F-14 | チームフィルタのラベル変更 | §1-6 | ✅ |
| F-15 | 関連ニュース表示 | §1-2・§1-3・§1-5・**§1-7** | ✅ |
| F-16 | 選手名・用語の表記統一 | §2-5 | ✅ |
| F-17 | ログインのレートリミット | §2-1-1・§2-4-2・§2-6・§2-7・**§4-2-1（429のUI）** | ✅ |
| F-18 | 日付パラメータのバリデーション | §2-1-2 | ✅ |
| F-19 | `datetime.utcnow()` の置換 | §2-3 | ✅ |
| F-20 | 外部リンクのスキーム検証 | §1-4-4 | ✅ |
| F-21 | CORS設定の限定 | §2-4-1（**`config.py` の定数に切り出し**）・§2-6 | ✅（基本設計書 v0.7 で是正済み） |

---

## 6. 手順5以降への引き継ぎ事項

| # | 引き継ぎ先 | 条件 | 内容 | 状態 |
|---|---|---|---|---|
| 1 | 手順5 | — | **`levenshtein.js` の単体テスト**。§1-2-3 の6ケースを最低限とし、**#1（`"NBA"` / `"NBAドラフト"` = 0.600）を必ず含める**（基本設計書§8 #9） | ⬜ |
| 2 | 手順5 | **要望1採用時** | **移行採用時のテストDBの扱い**（リスク調査書§5-2 #8・基本設計書§8 #5） | ⬜ |
| 3 | **基本設計書の次版** | — | **2件の是正**：①§4-5 の `allow_methods` を **`["GET","POST","PUT"]`** に（`PUT /api/settings` が使われている）、②§5-3 の `ENABLE_SCHEDULER` の分岐対象に **`shutdown_event()` の `scheduler.shutdown()`** を追加 | ✅**2026-09-01・基本設計書 v0.7 で反映**（DD-01／DD-02）。テスト設計書で**回帰テスト2件**を配置（T-P3-05 TC-05-3／T-P3-16 TC-16-5） |
| 4 | **改善バックログ** | — | `formatRelativeTime`（`NewsCard.jsx` L44-53）が `published_at` を**ローカル時刻として解釈**している。本フェーズの改修対象外だが、**経過時間が9時間ずれる可能性**がある。要件定義書§3-2の改善バックログ項目として記録 | ⬜ |
| 5 | 手順5 | — | **429 の分岐のテスト**（`useAuth.js` の `err.status` 付与と `LoginForm.jsx` の分岐）。実装・文言とも本書で確定済み（§4-2-1） | ⬜ |
| 6 | 手順5 | — | **Python側とJS側の Levenshtein 一致テスト**（基本設計書§8 #12）。§1-2-3 の数値例を共通の期待値とする。**サロゲートペアは対象外**（§1-2-2） | ⬜ |
| 7 | 手順7 | — | **`GLOSSARY` の主要選手20〜30名の確定**（§2-5）。要件定義書§3-4-2 の9件は本書に記載済み | ⬜ |
| 8 | **手順6の後** | **要望1採用時のみ** | 外部cron監視サービスの選定（基本設計書§8 #11）。本書は**呼び出し位置と条件のみ**を確定（§3-1） | ⬜ |
| 9 | 手順5 | **要望1採用時** | **`test_post_fetch()`（`tests/test_routes.py` L263-267）の削除**（基本設計書§8 #4）。削除対象は§3-5で特定済み。**実際の削除は採否確定後** | ⬜ |
| 10 | **先-1（2026年9月まで）** | — | **§3-2 の実施**（`config.py` の用途別分離）。要望1の採否に依存しない | ⬜ |
| 11 | 手順5 | — | **`tests/test_routes.py` L119 の `datetime.utcnow()` を置換**（§2-3）。F-19 の本番側と同時に行い、「置換した」という記録と実態を一致させる。`exp` は数値化されるため**テストの意味は変わらない** | ⬜ |
| **12** | **基本設計書の次版** | — | **DD-03**：**§1-2 のコンポーネント一覧に `App.jsx` を追加する**（レビューDD-R-01）。一覧11件は `App.jsx` を含んでおらず、**3文書（基本設計書§1-2・本書§1・テスト設計書§1-2-1）が同じ前提を共有していたため、どの工程でも検出されなかった**。DD-01／DD-02 と同じ扱い | ✅**2026-09-06・基本設計書 v0.8 で反映**。`App.jsx`（#12）に加え、**同じ理由で落ちていた3件**（`utils/constants.js`・`useAuth.js`／`LoginForm.jsx`・`api/limiter.py`）も #13〜#15 として追加された |
| **13** 🆕 | 手順7 | — | **`src/utils/constants.js`（新規）の作成**（§1-7-2 ①）。`EMPTY_SET` の1定数のみ。**読み取り専用として扱い `add` / `delete` を呼ばない**ことをコメントに残す | ⬜ |
| **14** 🆕 | **手順6の後** | **要望1採用時** | **T-P3-05（CORS）のフィクスチャを案B（`main.py` の `app` を import）へ移行するか再検討**（§2-4-1）。`ENABLE_SCHEDULER=false` が使えるようになるため選択肢が増える。**案Aのままでも成立する**ため必須ではない | ⬜ |

> **状態欄の運用**（基本設計書§8を踏襲）: 完了時は ✅ とし実施日を添える。**#10 は期限つき**である。
>
> **#3 の扱い**: 本書は**基本設計書の決定を変更しない**方針（§0-1）だが、この2件は**そのまま実装すると動かない**。本書では実装が壊れない値を採り、**基本設計書側の是正を引き継ぎ事項として明示する**（計画書§8-0 ③外方向）。**本書だけを直して基本設計書を放置すると、次に基本設計書を読んだ人が誤った値を実装する。**

---

## 変更履歴

| バージョン | 日付 | 変更内容 |
|---|---|---|
| v0.4 | 2026-09-06 | **レビュー結果報告書（`review_detail_design_p3_v0.3.txt`・🔴0件/🟡0件/🟢1件）の指摘1件を反映。** ①**DD3-01**：§2-1-1 に `api/limiter.py` のコードブロックが**2箇所**あった。v0.3 で「インスタンスはここだけで生成する」という位置づけを与えたブロックを節の冒頭に新設した際、**v0.2 の構成の名残であるブロックを消していなかった**。後半のブロックと、その直前の注記（「`main.py` で生成すると循環になる」——冒頭のブロックで既に解消済みの話）を削除し、**「独立モジュールに置く根拠」は冒頭のブロックの直後へ**、**「`app.state.limiter` への代入は `main.py` で行う」は `main.py` ブロックの直後へ**移した、②**§5-2 の判断項目の対象を「表」から「表・コードブロック」に拡張**。同一内容が2箇所にある問題は、本書§2-4-1 が CORS 定数で扱ったものと**同じ型**である（2箇所に書くと片方だけ更新して乖離する）。**確認方法としてコードブロックの機械抽出**を明記した——思いついた順に読むと同じ内容の2つ目を読み飛ばす、③**本版で🔴・🟡は3版連続0件**となり、残っていたのは体裁1件のみだった |
| v0.3 | 2026-09-06 | **レビュー結果報告書（`review_detail_design_p3_v0.2.txt`・🔴0件/🟡0件/🟢3件）の指摘3件を全件反映。** ①**DD2-01**：§2-1-1 の**コードブロックが直下の注記と食い違っていた**。注記は「`limiter` は `api/limiter.py` に置き両方がそこから import する」としながら、**`main.py` のブロックは `limiter = Limiter(...)` を独自に生成**していた。`slowapi` を実際に導入して挙動を確認したところ、**`_rate_limit_exceeded_handler` は `app.state.limiter` を読み、`@limiter.limit()` はデコレータ側の実体を使う**——`Limiter._headers_enabled` の既定が `False` のため**現状は実害が出ない**が、①**テストと本番で構成が食い違う**（テスト設計書§2-0 は `api.limiter` の実体を前提とする）、②`headers_enabled=True` にすると誤った残り回数を返す。コードブロックを注記に合わせ、**`api/routes.py` L1 に `Request` が無い**ことも明記（`slowapi` のデコレータは引数名 `request` の `Request` を要求するため、無いと `NameError`）、②**DD2-02**：§2-4-1 の案C が参照する `§6 #12` を **`#14`** に訂正（#12 は DD-03）。v0.2 で §6 に3行足した際に本文からの参照を追っていなかった、③**DD2-03**：§5-1 の参照先ファイル一覧に **`App.jsx`・`useAuth.js`・`LoginForm.jsx`・`utils/constants.js`** を追加。実在確認自体は照合リストで済んでいたが**一覧の記述が古いまま**で、**DD-R-01 の原因（古い一覧を出発点にする）と同じ形が本書にも残っていた**、④§5-1 の照合リストを **50件→51件**に拡張（`api/routes.py` L1）、A区分に「**§6 への番号参照を全件突き合わせる**」を追加、⑤**§5-2 に判断項目を2件新設**（例示コードと注記の整合／表に行を足したあと参照を追ったか） |
| v0.2 | 2026-09-06 | **レビュー結果報告書（`review_detail_design_p3_v0.1.txt`・🔴1件/🟡0件/🟢3件）の指摘4件と、テスト設計書レビュー TD-R-01 からの差し戻し1件を全件反映。** ①**DD-R-01（🔴）**：**§1-7『`App.jsx`（変更）』を新設**。`App.jsx` は `NewsCard` を描画する唯一のファイル（L87-96）であり、`useNews` の戻り値4件と `NewsCard` の props 7件をつなぐコードはここにしかない。本節がなければ **`isExpanded` が `undefined` になり全記事が永久に折りたたまれたまま**になる（例外が出ないため「実装したのに何も起きない」形で現れる）。あわせて **`relatedExpandedIds.get()` が `undefined` を返すのは通常状態**であることを明示し、**渡す側（§1-7）と受ける側（§1-5 のデフォルト引数）の両方**に `EMPTY_SET` を置いた。`Map`→`Set` の変換位置は3案比較のうえ `App.jsx` を採用。**`MainView` が非export である**ためテストは `App` を描画し `useAuth` をモックする方針も確定、②**TD-R-01 の差し戻し**：**CORS設定を `config.py` の定数（`CORS_ALLOW_METHODS`／`CORS_ALLOW_HEADERS`）に切り出す**（§2-4-1・§2-6）。v0.1 の直書きでは、テストフィクスチャが**テスト側に書いた値とテスト側に書いた値を比べる**形になり、**DD-01 と同じ乖離を検出できない**、③**DD-R-02（🟢）**：§2-7 に**条件欄**を設け `psycopg[binary]`（要望1採用時）を追加。あわせて **`sqlalchemy` を2.0系から下げない**注意を追記、④**DD-R-03（🟢）**：§1-2-3 の注記の素朴値を **0.571 → 0.429** に訂正（`0.571` は #6 kitten/sitting の値だった）。**訂正により差はむしろ拡大**するため設計判断は不変。テスト設計書 TC-08-1 も同時訂正、⑤**DD-R-04（🟢）**：§2-2-1 の追加 import を訂正（**`FetchLog` は L6 に既存で不要**・**`METRICS_WINDOW_DAYS` の追加指示が欠落**していた）。§5-1 の照合リストに `crud.py` L1-6 を追加、⑥§5-1 の照合リストを **43件→50件**に拡張（`crud.py` L1-6・`App.jsx` 4件）、⑦**§5-2 に判断項目を3件新設**（一覧表に載っていない実ファイルがないか／nullable を潰す場所を書いたか／指示の対象になっている行を照合したか）、⑧§6 に **DD-03（基本設計書§1-2 への `App.jsx` 追加）** ほか3件を追加 |
| v0.1 | 2026-09-01 | 初版作成。⓪**A区分（機械確認）が本文を3箇所変えた**：`allow_methods` と `PUT` の不整合（§2-4-1）／`tests/test_routes.py` L119 の `utcnow()` 残存（§2-3）／429 の分岐には `useAuth.js` の変更が要ること（§4-2-1）。①**F-13**：`expandedIds`（Set）・`relatedExpandedIds`（Map）を `useNews.js` に追加し、**一覧側の折りたたみのみが3状態すべてに触れる**実装を確定。副作用の**冪等性**を根拠にStrictModeの二重実行に耐える形とした、②**F-15**：`levenshtein.js`（**置換コスト2・`ratio()` と同一定義**）と `relatedness.js`（ゲート0.20・閾値0.35・上位5件）を新規設計。**手順5のための照合用数値例6件**を確定し、`RelatedNews` は **`NewsCard` を `isNested` 付きで再帰利用**する形にした（ネタバレ防止の実装を2箇所に持たない）、③**F-17**：`slowapi` の導入。**`request: Request` 引数が必須**であること、`limiter` を **`api/limiter.py` に分離**して循環importを避けることを確定、④**F-18**：`date` 型検証に加え **`.isoformat()` で crud に渡す**必要があることを明記（PostgreSQLでは型不一致になる）、⑤**F-19**：`python-jose` の `exp` の扱いを確認し **naive/aware の影響なし**と確定（§8 #2の消化）、⑥**F-20**：`new URL().protocol` による判定と**区切り文字ごと非表示**を確定、⑦**F-21**：⚠️**基本設計書の `["GET","POST"]` では `PUT /api/settings` が壊れる**ことを検出。実装値を `["GET","POST","PUT"]` とし、**基本設計書の是正**を§6 #3に引き継ぎ、⑧**§2-4-3**：⚠️`ENABLE_SCHEDULER` の分岐対象に **`shutdown_event()` が漏れていた**ことを検出（`SchedulerNotRunningError`）。同じく§6 #3に引き継ぎ、⑨**§3**：`run_batch_once.py`（**`log is None` も失敗**・ping失敗は終了コードに影響させない）・`config.py` の用途別分離・`batch.yml`・`models.py` の接続URL化を設計、⑩基本設計書§8の**13件を§0-2で全件追跡**し、手順5・6・7への引き継ぎ10件を§6に整理 |
