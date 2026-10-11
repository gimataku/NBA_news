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

# GitHub Actions のログに進行状況を残す（詳細設計書§3-3 の注記「標準出力のみ」を実現する）
# ファイル出力は設定しない（logs/ を作らない。os.makedirs は main.py にしかない）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)

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
