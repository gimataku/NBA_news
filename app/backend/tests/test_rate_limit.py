"""T-P3-01: ログインのレートリミット（F-17）"""
from config import INIT_USERNAME, INIT_USER_PASSWORD, LOGIN_RATE_LIMIT
from db import crud

# 制限回数は本番の定数から導く（"5/minute" → 5）
LIMIT = int(LOGIN_RATE_LIMIT.split("/")[0])


def _init_user():
    """テスト用ユーザーをDBに作成する"""
    from auth.users import init_user
    init_user(crud)


def _login(client, password):
    return client.post(
        "/api/auth/login",
        json={"username": INIT_USERNAME, "password": password},
    )


# ── T-P3-01 ──────────────────────────────────────────────────────────────────

def test_tc_p3_01_1_login_success_once(raw_api_client):
    """TC-01-1: 正しい認証情報で1回ログイン → HTTP 200 / access_token あり"""
    _init_user()

    resp = _login(raw_api_client, INIT_USER_PASSWORD)

    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_tc_p3_01_2_wrong_password_up_to_limit(raw_api_client):
    """TC-01-2: 誤った認証情報で制限回数まで連続 → すべて HTTP 401（429 にならない）"""
    _init_user()

    statuses = [_login(raw_api_client, "wrongpass_XYZ").status_code for _ in range(LIMIT)]

    assert statuses == [401] * LIMIT


def test_tc_p3_01_3_wrong_password_over_limit(raw_api_client):
    """TC-01-3: 誤った認証情報で制限回数+1回連続 → 1〜制限回数目 401・超過分 429"""
    _init_user()

    statuses = [_login(raw_api_client, "wrongpass_XYZ").status_code for _ in range(LIMIT + 1)]

    assert statuses == [401] * LIMIT + [429]


def test_tc_p3_01_4_correct_password_after_limit(raw_api_client):
    """TC-01-4: TC-01-3 の直後に正しい認証情報で1回 → HTTP 429（成否ではなくリクエスト数で制限）"""
    _init_user()
    for _ in range(LIMIT + 1):
        _login(raw_api_client, "wrongpass_XYZ")

    resp = _login(raw_api_client, INIT_USER_PASSWORD)

    assert resp.status_code == 429


def test_tc_p3_01_5_other_endpoints_not_limited(api_client):
    """TC-01-5: GET /api/news を制限回数+1回連続 → いずれも 429 にならない"""
    statuses = [api_client.get("/api/news").status_code for _ in range(LIMIT + 1)]

    assert 429 not in statuses
    assert statuses == [200] * (LIMIT + 1)


def test_tc_p3_01_6_no_lockout(raw_api_client):
    """TC-01-6: 429 の前後で users テーブルが変化しない（ロックアウトしない）"""
    _init_user()
    count_before = crud.count_users()
    user_before = crud.get_user(INIT_USERNAME)

    statuses = [_login(raw_api_client, "wrongpass_XYZ").status_code for _ in range(LIMIT + 1)]
    assert statuses[-1] == 429

    assert crud.count_users() == count_before
    assert crud.get_user(INIT_USERNAME) == user_before


# ── キー関数 get_client_ip の単体テスト（F8 対処・7-A-4c） ─────────────────────

def _request(headers=None, client=("9.9.9.9", 1234)):
    from starlette.requests import Request
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    return Request({"type": "http", "headers": raw, "client": client})


def test_k_1_cf_connecting_ip_only():
    """K-1: CF-Connecting-IP のみ → その値"""
    from api.limiter import get_client_ip
    assert get_client_ip(_request({"CF-Connecting-IP": "1.1.1.1"})) == "1.1.1.1"


def test_k_2_cf_connecting_ip_takes_precedence():
    """K-2: CF-Connecting-IP と X-Forwarded-For → CF が優先"""
    from api.limiter import get_client_ip
    req = _request({
        "CF-Connecting-IP": "1.1.1.1",
        "X-Forwarded-For": "2.2.2.2, 3.3.3.3, 4.4.4.4",
    })
    assert get_client_ip(req) == "1.1.1.1"


def test_k_3_xff_second_from_right():
    """K-3: X-Forwarded-For のみ → 右から2番目（先頭の偽装値は使わない）"""
    from api.limiter import get_client_ip
    req = _request({"X-Forwarded-For": "spoof, 5.5.5.5, 6.6.6.6"})
    assert get_client_ip(req) == "5.5.5.5"


def test_k_4_xff_single_element_falls_back_to_client_host():
    """K-4: X-Forwarded-For が1要素 → request.client.host"""
    from api.limiter import get_client_ip
    assert get_client_ip(_request({"X-Forwarded-For": "7.7.7.7"})) == "9.9.9.9"


def test_k_5_no_headers_falls_back_to_client_host():
    """K-5: ヘッダなし → request.client.host"""
    from api.limiter import get_client_ip
    assert get_client_ip(_request()) == "9.9.9.9"


def test_k_6_no_client_no_headers():
    """K-6: request.client が None・ヘッダなし → "unknown" """
    from api.limiter import get_client_ip
    assert get_client_ip(_request(client=None)) == "unknown"


# ── キー関数の結合テスト（F8 対処・7-A-4c） ──────────────────────────────────

def _login_with_headers(client, password, headers):
    return client.post(
        "/api/auth/login",
        json={"username": INIT_USERNAME, "password": password},
        headers=headers,
    )


def test_tc_p3_01_7_xff_spoofing_does_not_bypass(raw_api_client):
    """TC-01-7（F8 の回帰）: X-Forwarded-For の先頭を毎回変えても同じバケット → 1〜制限回数目 401・超過分 429"""
    _init_user()

    statuses = [
        _login_with_headers(
            raw_api_client,
            "wrongpass_XYZ",
            {"X-Forwarded-For": f"spoof{i}, 203.0.113.50, 198.51.100.1"},
        ).status_code
        for i in range(LIMIT + 1)
    ]

    assert statuses == [401] * LIMIT + [429]


def test_tc_p3_01_8_limit_is_per_ip(raw_api_client):
    """TC-01-8（IP 単位）: 1つ目のクライアントが 429 になっても、2つ目のクライアントは 401（別バケット）"""
    _init_user()

    statuses = [
        _login_with_headers(
            raw_api_client, "wrongpass_XYZ", {"CF-Connecting-IP": "203.0.113.1"}
        ).status_code
        for _ in range(LIMIT + 1)
    ]
    assert statuses[-1] == 429

    resp = _login_with_headers(
        raw_api_client, "wrongpass_XYZ", {"CF-Connecting-IP": "203.0.113.2"}
    )

    assert resp.status_code == 401
