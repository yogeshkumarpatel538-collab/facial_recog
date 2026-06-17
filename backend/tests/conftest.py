import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.user import User, UserRole
from app.utils.security import hash_password

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TEST_PASSWORD = "SecurePass1"


@pytest.fixture(autouse=True)
def disable_redis(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "redis_enabled", False)


@pytest.fixture(autouse=True)
def sync_test_database_engine(monkeypatch):
    """Ensure WebSocket auth and API share the same in-memory test database."""
    monkeypatch.setattr("app.database.session.engine", engine)
    monkeypatch.setattr("app.database.session.SessionLocal", TestingSessionLocal)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def viewer_user(db_session):
    user = User(
        email="viewer@example.com",
        password_hash=hash_password(TEST_PASSWORD),
        role=UserRole.VIEWER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    user = User(
        email="admin@example.com",
        password_hash=hash_password(TEST_PASSWORD),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def viewer_token(client, viewer_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": viewer_user.email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
