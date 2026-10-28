import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.limiter import limiter
from api.routes import router as api_router
from auth.users import init_user
from config import CORS_ALLOW_HEADERS, CORS_ALLOW_METHODS
from db import crud
from db.models import init_db
from scheduler import check_and_run_batch, scheduler

# logsディレクトリの自動作成（起動時に存在しない場合に生成）
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/nba_news.log"),
    ],
)

logger = logging.getLogger(__name__)

app = FastAPI(title="NBA News JP")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS設定（ローカル開発時は localhost:5173、本番はALLOWED_ORIGINS環境変数で指定）
_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
_origins = [o.strip() for o in _origins_env.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

app.include_router(api_router, prefix="/api")


@app.get("/healthz")
def healthz():
    """認証不要のヘルスチェック（Renderのヘルスチェックパスに使用）"""
    return {"status": "ok"}


def _scheduler_enabled() -> bool:
    """ENABLE_SCHEDULER が "false"（大文字小文字不問）以外なら有効（未設定時は有効）"""
    return os.getenv("ENABLE_SCHEDULER", "true").lower() != "false"


@app.on_event("startup")
def startup_event() -> None:
    init_db()
    logger.info("DB initialized")
    init_user(crud)
    logger.info("Initial user check completed")
    if _scheduler_enabled():
        scheduler.start()
        logger.info("Scheduler started")
        check_and_run_batch()
    else:
        logger.info("Scheduler disabled (ENABLE_SCHEDULER=false)")

    # TEMP（SEC-1）：eMudhra 証明書拒否の確認。確認後に削除する。
    import requests as _rq
    for _u in ("https://dv-g3b-emudhra.we-have-a-problem.com/",
               "https://dv-g3b-aaa-emudhra.we-have-a-problem.com/"):
        try:
            _r = _rq.get(_u, timeout=5)
            logger.error("SEC-1 NG reachable %s %s", _r.status_code, _u)
        except _rq.exceptions.SSLError:
            logger.info("SEC-1 OK rejected %s", _u)
        except Exception as _e:
            logger.warning("SEC-1 ?? %s %s", type(_e).__name__, _u)


@app.on_event("shutdown")
def shutdown_event() -> None:
    if _scheduler_enabled():
        scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
        reload=False,
    )
