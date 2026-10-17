"""T-P3-05: CORS の許可メソッド・ヘッダの限定（F-21）"""
ALLOWED_ORIGIN = "http://localhost:5173"


def _preflight(client, method, origin=ALLOWED_ORIGIN, request_headers=None):
    headers = {"Origin": origin, "Access-Control-Request-Method": method}
    if request_headers:
        headers["Access-Control-Request-Headers"] = request_headers
    return client.options("/api/settings", headers=headers)


# ── T-P3-05 ──────────────────────────────────────────────────────────────────

def test_tc_p3_05_1_preflight_get_allowed(cors_client):
    """TC-05-1: プリフライト GET → 200・Allow-Methods に GET"""
    resp = _preflight(cors_client, "GET")
    assert resp.status_code == 200
    assert "GET" in resp.headers["access-control-allow-methods"]


def test_tc_p3_05_2_preflight_post_allowed(cors_client):
    """TC-05-2: プリフライト POST → 200・Allow-Methods に POST"""
    resp = _preflight(cors_client, "POST")
    assert resp.status_code == 200
    assert "POST" in resp.headers["access-control-allow-methods"]


def test_tc_p3_05_3_preflight_put_allowed(cors_client):
    """TC-05-3: プリフライト PUT → 200・Allow-Methods に PUT（設定保存の回帰）"""
    resp = _preflight(cors_client, "PUT")
    assert resp.status_code == 200
    assert "PUT" in resp.headers["access-control-allow-methods"]


def test_tc_p3_05_4_preflight_delete_rejected(cors_client):
    """TC-05-4: プリフライト DELETE → 400・Allow-Methods に DELETE を含まない"""
    resp = _preflight(cors_client, "DELETE")
    assert resp.status_code == 400
    assert "DELETE" not in resp.headers.get("access-control-allow-methods", "")


def test_tc_p3_05_5_preflight_patch_rejected(cors_client):
    """TC-05-5: プリフライト PATCH → 400・Allow-Methods に PATCH を含まない"""
    resp = _preflight(cors_client, "PATCH")
    assert resp.status_code == 400
    assert "PATCH" not in resp.headers.get("access-control-allow-methods", "")


def test_tc_p3_05_6_preflight_authorization_header_allowed(cors_client):
    """TC-05-6: Request-Headers: Authorization → 200"""
    resp = _preflight(cors_client, "PUT", request_headers="Authorization")
    assert resp.status_code == 200


def test_tc_p3_05_7_preflight_content_type_header_allowed(cors_client):
    """TC-05-7: Request-Headers: Content-Type → 200"""
    resp = _preflight(cors_client, "PUT", request_headers="Content-Type")
    assert resp.status_code == 200


def test_tc_p3_05_8_preflight_custom_header_rejected(cors_client):
    """TC-05-8: Request-Headers: X-Custom-Header → 400"""
    resp = _preflight(cors_client, "PUT", request_headers="X-Custom-Header")
    assert resp.status_code == 400


def test_tc_p3_05_9_preflight_disallowed_origin(cors_client):
    """TC-05-9: 許可外オリジン → 400・Allow-Origin が返らない"""
    resp = _preflight(cors_client, "GET", origin="https://evil.example")
    assert resp.status_code == 400
    assert "access-control-allow-origin" not in resp.headers


def test_tc_p3_05_10_actual_put_settings(cors_client):
    """TC-05-10: 実リクエスト PUT /api/settings → 200・Allow-Origin が返る"""
    resp = cors_client.put(
        "/api/settings",
        json={"spoiler_guard_enabled": False},
        headers={"Origin": ALLOWED_ORIGIN},
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


def test_tc_p3_05_11_main_cors_options_match_config():
    """TC-05-11: main.app の CORSMiddleware の設定が config の定数と一致する"""
    import main
    from config import CORS_ALLOW_HEADERS, CORS_ALLOW_METHODS
    mw = next(m for m in main.app.user_middleware if m.cls.__name__ == "CORSMiddleware")
    assert mw.kwargs["allow_methods"] == CORS_ALLOW_METHODS
    assert mw.kwargs["allow_headers"] == CORS_ALLOW_HEADERS
