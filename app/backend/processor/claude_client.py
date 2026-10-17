import json
import logging
import re
import time

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_INTERVAL, CLAUDE_MAX_TOKENS, CLAUDE_MODEL
from db import crud

logger = logging.getLogger(__name__)

# クライアントはモジュールレベルで1度だけ初期化する
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """あなたはNBAニュースの翻訳・要約・分類アシスタントです。
必ずJSON形式のみで回答してください。マークダウンや説明文は不要です。"""

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

USER_PROMPT_TEMPLATE = """以下のNBAニュース記事を処理してください。

タイトル: {title}
本文抜粋: {description}

以下のJSON形式で回答してください：
{{
  "title_ja": "日本語に翻訳した見出し（原文のニュアンスを保持）",
  "summary_ja": "800〜1200字の日本語要約",
  "category": "trade_fa または draft または injury または column",
  "has_score": true または false
}}

【分類ルール】
- trade_fa : トレード・移籍・FA・契約情報（旧 trade + contract を統合）
- draft    : ドラフト候補・指名・撤退情報
- injury   : インジャリーレポート・欠場・復帰情報
- column   : 試合分析・試合速報・スコア記事・選手評価・戦術・インタビュー・その他
             ※ 試合結果・スコアが主要情報の記事も column に分類すること（game カテゴリはなし）

【重要ルール】
- has_score は本文に具体的な得点数値が含まれる場合のみ true
- has_score=true のルールはカテゴリを問わず適用する（column でも true になりうる）
- JSON 以外の文字列を出力しないこと""" + GLOSSARY


def process_article(title: str, description: str) -> dict | None:
    """
    Returns: {"title_ja": str, "summary_ja": str, "category": str, "has_score": bool}
    失敗時: None（呼び出し元でスキップ処理）
    """
    try:
        response = anthropic_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    title=title,
                    description=description[:1000],  # 最大1000文字に制限
                ),
            }],
        )
        raw = response.content[0].text.strip()
        # ```json ... ``` フェンスが含まれる場合は除去
        raw = re.sub(r"^```json\s*|\s*```$", "", raw, flags=re.MULTILINE)
        result = json.loads(raw)

        # バリデーション
        assert result["category"] in ("trade_fa", "draft", "injury", "column")
        assert isinstance(result["has_score"], bool)
        return result

    except anthropic.RateLimitError:
        crud.set_setting("api_limit_exceeded", "true")
        return None

    except (json.JSONDecodeError, KeyError, AssertionError):
        logger.warning("Claude response parse error: %s", title)
        return None

    except anthropic.APIError as exc:
        logger.error("Claude API error for '%s': %s", title, exc)
        return None

    finally:
        time.sleep(CLAUDE_INTERVAL)  # 例外発生時もインターバルを確保
