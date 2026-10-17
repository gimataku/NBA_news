"""T-P3-04: JWT の有効期限（F-19）"""
from datetime import datetime, timedelta, timezone

from jose import jwt as jose_jwt

from auth.jwt import create_access_token, verify_token
from config import ACCESS_TOKEN_EXPIRE_DAYS, JWT_ALGORITHM, SECRET_KEY


# ── T-P3-04 ──────────────────────────────────────────────────────────────────

def test_tc_p3_04_1_issue_and_verify():
    """TC-04-1: 発行したトークンを検証 → sub が返る"""
    token = create_access_token({"sub": "u"})
    assert verify_token(token) == "u"


def test_tc_p3_04_2_expired_token():
    """TC-04-2: exp が過去のトークン → None"""
    token = jose_jwt.encode(
        {"sub": "u", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
        SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    assert verify_token(token) is None


def test_tc_p3_04_3_exp_is_now_plus_expire_days():
    """TC-04-3: 発行直後の exp → 現在時刻＋ACCESS_TOKEN_EXPIRE_DAYS 日（±10秒）"""
    token = create_access_token({"sub": "u"})
    payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

    expected = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    assert abs(payload["exp"] - expected.timestamp()) <= 10


def test_tc_p3_04_4_tampered_token():
    """TC-04-4: 改ざんしたトークン → None"""
    token = create_access_token({"sub": "u"})
    header, payload, signature = token.split(".")
    tampered_sig = ("A" if signature[0] != "A" else "B") + signature[1:]
    assert verify_token(f"{header}.{payload}.{tampered_sig}") is None
