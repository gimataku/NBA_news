"""T-P3-06: 選手名・用語の表記統一（GLOSSARY）"""
import re

from processor.claude_client import GLOSSARY, USER_PROMPT_TEMPLATE

# 要件定義書§3-4-2 の確定済み9件
CONFIRMED_TERMS = [
    "デローザン",
    "バランチューナス",
    "タイラー・ヒーロー",
    "ヴィクター・ウェンバンヤマ",
    "ケレル・ウェア",
    "マルアチ",
    "ヤニス",
    "マティス・サイブル",
    "エプロン",
]


def _formatted() -> str:
    return USER_PROMPT_TEMPLATE.format(title="t", description="d")


def test_tc06_1_format_does_not_raise():
    """TC-06-1: GLOSSARY 連結後も format() が例外を投げないこと"""
    assert _formatted()


def test_tc06_1b_glossary_has_no_braces():
    """TC-06-1b: GLOSSARY に波括弧が含まれないこと（format() の KeyError 防止）"""
    assert "{" not in GLOSSARY and "}" not in GLOSSARY


def test_tc06_2_confirmed_terms_included():
    """TC-06-2: 確定済み9件の日本語表記がすべて含まれること"""
    prompt = _formatted()
    for term in CONFIRMED_TERMS:
        assert term in prompt, term


def test_tc06_3_instruction_included():
    """TC-06-3: 表記ルールの指示文が含まれること"""
    assert "以下の表にある語は、必ず「日本語表記」の列の表記に従うこと。" in _formatted()


def test_tc06_5_no_duplicate_english_entries():
    """TC-06-5: 表の英語列に重複がないこと"""
    rows = re.findall(r"^\| (.+?) \| (.+?) \|$", GLOSSARY, flags=re.MULTILINE)
    english = [en for en, _ in rows if en != "英語"]
    assert english
    assert len(english) == len(set(english))
