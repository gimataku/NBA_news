import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test.db"))

# シェルや .env の実値に左右されないよう無条件に上書きする
os.environ["ANTHROPIC_API_KEY"]   = "sk-ant-test-dummy-key"
os.environ["BALLDONTLIE_API_KEY"] = "test-dummy-key"
os.environ["SECRET_KEY"]          = "test-secret-key-for-testing-purposes-only-32chars"
os.environ["USERNAME"]            = "testuser"
os.environ["USER_PASSWORD"]       = "testpass123"
os.environ["DATABASE_URL"]        = "sqlite:///test_dummy.db"   # 本番URLが混入しても collection が壊れないようにする（実際のテストは conftest 自前のエンジンを使うため値は使われない）


@pytest.fixture(scope="session", autouse=True)
def patch_db_session():
    import db.models as models_module
    import db.crud as crud_module

    test_engine = create_engine(
        f"sqlite:///{TEST_DB_PATH}",
        connect_args={"check_same_thread": False},
    )
    TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

    original_engine = models_module.engine
    original_models_sl = models_module.SessionLocal
    original_crud_sl = crud_module.SessionLocal

    models_module.engine = test_engine
    models_module.SessionLocal = TestSessionLocal
    crud_module.SessionLocal = TestSessionLocal

    models_module.Base.metadata.create_all(bind=test_engine)

    yield test_engine, TestSessionLocal

    models_module.engine = original_engine
    models_module.SessionLocal = original_models_sl
    crud_module.SessionLocal = original_crud_sl
    test_engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(autouse=True)
def reset_db(patch_db_session):
    test_engine, TestSessionLocal = patch_db_session
    import db.models as models_module
    from db.models import AppSetting

    models_module.Base.metadata.drop_all(bind=test_engine)
    models_module.Base.metadata.create_all(bind=test_engine)

    with TestSessionLocal() as session:
        for key, value in [
            ("spoiler_guard_enabled",    "true"),
            ("spurs_filter_enabled",     "false"),
            ("last_fetched_at",          ""),
            ("api_limit_exceeded",       "false"),
            ("api_reset_month",          ""),
            ("last_schedule_fetched_at", ""),
        ]:
            session.add(AppSetting(key=key, value=value))
        session.commit()

    yield


@pytest.fixture(autouse=True)
def reset_rate_limit():
    from api.limiter import limiter
    limiter.reset()
    yield


@pytest.fixture
def api_client(reset_db):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from api.limiter import limiter
    from api.routes import get_current_user, router

    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_current_user] = lambda: "testuser"
    with TestClient(app) as client:
        yield client


@pytest.fixture
def raw_api_client(reset_db):
    """JWT認証オーバーライドなしのテストクライアント（認証テスト用）"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from api.limiter import limiter
    from api.routes import router

    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(router, prefix="/api")
    with TestClient(app) as client:
        yield client


@pytest.fixture
def cors_client(reset_db):
    """本番と同じ CORS 定数（config）を適用したテストクライアント（F-21・T-P3-05 用）"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.testclient import TestClient
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from api.limiter import limiter
    from api.routes import get_current_user, router
    from config import CORS_ALLOW_HEADERS, CORS_ALLOW_METHODS

    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_current_user] = lambda: "testuser"
    with TestClient(app) as client:
        yield client
