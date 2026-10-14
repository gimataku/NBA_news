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
