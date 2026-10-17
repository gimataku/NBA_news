# 実装指示 7-A-7：F-16 選手名・用語の表記統一（`GLOSSARY` の新設）

作成日：2026-10-17 ／ 主担当：Claude Code ／ 根拠：要件定義書§3-4、詳細設計書§2-5、テスト設計書 T-P3-06、候補表 `glossary_candidates_7-A-7.md`（Takumi様確認済み）
🔴 `.env` は読まない。変更するのは `backend/processor/claude_client.py` と新規テスト1ファイルのみ。

## 1. 変更内容（`processor/claude_client.py`）

1. 定数 **`GLOSSARY`** を `USER_PROMPT_TEMPLATE` の**直前**に新設し、`USER_PROMPT_TEMPLATE` の定義の末尾に **`+ GLOSSARY`** で連結する（詳細設計書§2-5のとおり。`SYSTEM_PROMPT` には入れない）。
2. 🔴 **`GLOSSARY` に `{` `}` を含めない**。連結後の文字列に `USER_PROMPT_TEMPLATE.format()`（`process_article` 内）がかかるため、波括弧があると**実行時に `KeyError` でバッチ全体が止まる**。
3. `process_article()` 本体・既存プロンプト（`SYSTEM_PROMPT`、`USER_PROMPT_TEMPLATE` の既存部分）は**一切変更しない**。
4. 連結位置の注意：現行テンプレートは `…JSON 以外の文字列を出力しないこと"""` で終わる。`GLOSSARY` の先頭は**改行から始める**（直前の行と同じ行に連結しない）。

### `GLOSSARY` の内容（そのまま使う。表記は Takumi様確認済み。**人数を絞った最終版＝38行**）

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
| De'Aaron Fox | デアーロン・フォックス |
| Stephon Castle | ステフォン・キャッスル |
| Devin Vassell | デビン・ヴァセル |
| Harrison Barnes | ハリソン・バーンズ |
| Dylan Harper | ディラン・ハーパー |
| Keldon Johnson | ケルドン・ジョンソン |
| Julian Champagnie | ジュリアン・シャンペニー |
| Jeremy Sochan | ジェレミー・ソーハン |
| Chris Paul | クリス・ポール |
| Mitch Johnson | ミッチ・ジョンソン |
| Jordan McLaughlin | ジョーダン・マクラフリン |
| David Jones García | デビット・ジョーンズ・ガルシア |
| Ja'Kobi Gillespie | ジャコビ・ギレスピー |
| Tobias Harris | トバイアス・ハリス |
| Carter Bryant | カーター・ブライアント |
| Jayden Quaintance | ジェイデン・クインタンズ |
| Maliq Brown | マリーク・ブラウン |
| Luke Kornet | ルーク・コーネット |
| Tarris Reed Jr. | タリス・リードジュニア |
| Billy Donovan | ビリー・ドノバン |
| Giannis Antetokounmpo | ヤニス・アデトクンボ |
| Shams Charania | シャムズ・シャラニア |
| Luka Dončić | ルカ・ドンチッチ |
| Shai Gilgeous-Alexander | シェイ・ギルジャス＝アレキサンダー |
| Malaki Branham | マラカイ・ブランナム |
| Ivica Zubac | イビチャ・ズバッツ |
| Jalen Brunson | ジェイレン・ブランソン |
| Ochai Agbaji | オチャイ・アバジ |
| Zuby Ejiofor | ズビー・エジフォー |
"""
```

### 候補表からの調整（Claude の判断。Takumi様は報告で確認）
| 内容 | 扱い |
|---|---|
| `Dylan Harper` が #5 と #11 で**重複** | **1行に統合** |
| `ルーク・コ―ネット` の「―」が**長音記号ではなく罫線風のダッシュ（U+2015）** | **`ー`（U+30FC）に直して `コーネット`** |
| #14 `David Jones García`：Takumi様回答「デビット・ジョンーズ・ガルシア」 | **`デビット・ジョーンズ・ガルシア` として収録**（「ジョンーズ」は「ジョーンズ」の誤記と判断。「デビット」は Takumi様の表記のまま）。報告で Takumi様が最終確認 |
| Takumi様が候補表から削除した選手（Connaughton・Embiid・Morant・Porziņģis・Şengün） | **入れない**（上の `GLOSSARY` は削除後の最終版）。候補表（最新版）と突合し、差異を報告 |

## 2. テスト（新規 `tests/test_glossary.py`）— 手順8に回さず今回追加する
**根拠**：`KeyError` は本番バッチを止める事故に直結し、push 後の自動デプロイ・次回バッチで即座に影響するため（T-P3-04/05 と同様に前倒し）。訳語の正しさはテストしない（Claude API 依存。設計書どおり）。

| ケース | 内容 |
|---|---|
| TC-06-1 | `USER_PROMPT_TEMPLATE.format(title="t", description="d")` が**例外を投げない** |
| TC-06-1b | `"{" not in GLOSSARY and "}" not in GLOSSARY` |
| TC-06-2 | 整形後の文字列に、要件定義書§3-4-2 の**9件の日本語表記**（`デローザン`・`バランチューナス`・`タイラー・ヒーロー`・`ヴィクター・ウェンバンヤマ`・`ケレル・ウェア`・`マルアチ`・`ヤニス`・`マティス・サイブル`・`エプロン`）がすべて含まれる |
| TC-06-3 | 整形後の文字列に「**表にある語は、必ず**」相当の文言（`GLOSSARY` の指示文そのもの）が含まれる |
| TC-06-5 | `GLOSSARY` の表の行（`\| … \| … \|` 形式）の**英語列に重複がない**（今回の重複混入の再発防止） |
| TC-06-4 | 既存の `process_article` 系テスト（モック）が**変更なしで通る**ことを全体実行で確認（新規作成は不要） |

## 3. 検証
| # | 確認 | 期待 |
|---|---|---|
| 1 | `cd app/backend`、`DATABASE_URL` を外して `pytest` | 全件 passed（現在 133 → 追加分を足した件数。件数を報告） |
| 2 | `git diff --stat` | `claude_client.py` と `tests/test_glossary.py`（新規）のみ |
| 3 | `python -c "from processor.claude_client import USER_PROMPT_TEMPLATE as T; print(len(T.format(title='t',description='d')))"` で長さを出し、**増加した文字数**を報告（概算トークン数＝日本語は約1〜1.5トークン/文字として見積もる） | 例外なし |
| 4 | `grep -n "GLOSSARY" processor/claude_client.py` | 定義1・連結1 |
| 5 | 全角ダッシュ混入確認：`grep -n "―" processor/claude_client.py` | 0 件 |

## 4. 報告
1. diff（全文）／2. pytest 件数／3. 検証 #3 の増加量と見積もり（設計書の「約200〜400トークン」を**超える場合はその旨**。収録が 38 行（選手・関係者 29 名＋確定9件の語を含む）で、設計の想定と近いが念のため）／4. 候補表との突合結果（欠落・追加した行）。
**実APIは叩かない。** commit は Takumi様。push 後の初回バッチで翻訳が正常に動くこと（Actions が成功し記事が増える）は Takumi様が確認する。
