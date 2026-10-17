"""T-P3-02: /api/schedule の日付検証（F-18）"""
from datetime import datetime, timezone

from db.models import GameSchedule


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _insert_game(session, game_id: str, game_date: str):
    session.add(GameSchedule(
        game_id=game_id,
        game_date=game_date,
        status="Scheduled",
        home_team="SAS",
        visitor_team="LAL",
        has_score=0,
        fetched_at=_now_str(),
    ))


# ── T-P3-02 ──────────────────────────────────────────────────────────────────

def test_tc_p3_02_1_valid_range_returns_games_in_range(api_client, patch_db_session):
    """TC-02-1: 正しい日付範囲 → HTTP 200・期間内の試合のみ返る"""
    _, TestSessionLocal = patch_db_session
    with TestSessionLocal() as session:
        _insert_game(session, "in1", "2026-09-03")
        _insert_game(session, "in2", "2026-09-05")
        _insert_game(session, "before", "2026-08-31")
        _insert_game(session, "after", "2026-09-08")
        session.commit()

    resp = api_client.get(
        "/api/schedule",
        params={"start_date": "2026-09-01", "end_date": "2026-09-07"},
    )

    assert resp.status_code == 200
    assert sorted(g["game_id"] for g in resp.json()["games"]) == ["in1", "in2"]


def test_tc_p3_02_2_invalid_month(api_client):
    """TC-02-2: 月が不正（2026-13-01）→ HTTP 422"""
    resp = api_client.get(
        "/api/schedule",
        params={"start_date": "2026-13-01", "end_date": "2026-09-07"},
    )
    assert resp.status_code == 422


def test_tc_p3_02_3_non_date_string(api_client):
    """TC-02-3: 日付でない文字列（abc）→ HTTP 422"""
    resp = api_client.get(
        "/api/schedule",
        params={"start_date": "abc", "end_date": "2026-09-07"},
    )
    assert resp.status_code == 422


def test_tc_p3_02_4_missing_start_date(api_client):
    """TC-02-4: start_date を省略 → HTTP 422"""
    resp = api_client.get("/api/schedule", params={"end_date": "2026-09-07"})
    assert resp.status_code == 422


def test_tc_p3_02_5_reversed_range_returns_empty(api_client, patch_db_session):
    """TC-02-5: start_date > end_date → HTTP 200・空配列（逆転の検証はしない）"""
    _, TestSessionLocal = patch_db_session
    with TestSessionLocal() as session:
        _insert_game(session, "g1", "2026-09-03")
        session.commit()

    resp = api_client.get(
        "/api/schedule",
        params={"start_date": "2026-09-07", "end_date": "2026-09-01"},
    )

    assert resp.status_code == 200
    assert resp.json()["games"] == []


def test_tc_p3_02_6_boundary_dates_inclusive(api_client, patch_db_session):
    """TC-02-6: game_date が start_date・end_date と完全一致 → 両方とも含まれる（.isoformat() の検証を兼ねる）"""
    _, TestSessionLocal = patch_db_session
    with TestSessionLocal() as session:
        _insert_game(session, "start", "2026-09-01")
        _insert_game(session, "end", "2026-09-07")
        session.commit()

    resp = api_client.get(
        "/api/schedule",
        params={"start_date": "2026-09-01", "end_date": "2026-09-07"},
    )

    assert resp.status_code == 200
    assert sorted(g["game_id"] for g in resp.json()["games"]) == ["end", "start"]
