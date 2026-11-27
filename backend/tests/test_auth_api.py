import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models.user import User


@pytest.fixture
def auth_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_register_success(auth_client: TestClient):
    response = auth_client.post(
        "/auth/register",
        json={
            "email": "student@careerlens.dev",
            "name": "Aaditya Soni",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "student@careerlens.dev"
    assert data["user"]["name"] == "Aaditya Soni"
    assert "id" in data["user"]


def test_register_duplicate_email_returns_409(auth_client: TestClient):
    payload = {
        "email": "duplicate@careerlens.dev",
        "name": "Jane Doe",
        "password": "Password123456!",
    }
    first_res = auth_client.post("/auth/register", json=payload)
    assert first_res.status_code == 201

    second_res = auth_client.post("/auth/register", json=payload)
    assert second_res.status_code == 409
    assert "already exists" in second_res.json()["detail"].lower()


def test_register_short_password_fails_validation(auth_client: TestClient):
    response = auth_client.post(
        "/auth/register",
        json={
            "email": "short@careerlens.dev",
            "name": "Short Pass",
            "password": "short",
        },
    )
    assert response.status_code == 422


def test_login_success(auth_client: TestClient):
    # Register first
    auth_client.post(
        "/auth/register",
        json={
            "email": "login@careerlens.dev",
            "name": "Login User",
            "password": "SecurePassword123!",
        },
    )

    # Login with exact credentials
    login_res = auth_client.post(
        "/auth/login",
        json={
            "email": "login@careerlens.dev",
            "password": "SecurePassword123!",
        },
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == "login@careerlens.dev"


def test_login_invalid_password_returns_401(auth_client: TestClient):
    auth_client.post(
        "/auth/register",
        json={
            "email": "wrongpass@careerlens.dev",
            "name": "Wrong Pass User",
            "password": "SecurePassword123!",
        },
    )

    response = auth_client.post(
        "/auth/login",
        json={
            "email": "wrongpass@careerlens.dev",
            "password": "IncorrectPassword999!",
        },
    )
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


def test_login_nonexistent_user_returns_401(auth_client: TestClient):
    response = auth_client.post(
        "/auth/login",
        json={
            "email": "nonexistent@careerlens.dev",
            "password": "SomePassword123!",
        },
    )
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


def test_me_endpoint_with_valid_and_invalid_token(auth_client: TestClient):
    # Unauthenticated request
    unauth_res = auth_client.get("/auth/me")
    assert unauth_res.status_code == 401

    # Invalid token
    invalid_res = auth_client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert invalid_res.status_code == 401

    # Register and get real token
    reg_res = auth_client.post(
        "/auth/register",
        json={
            "email": "me@careerlens.dev",
            "name": "Me User",
            "password": "SecurePassword123!",
        },
    )
    token = reg_res.json()["access_token"]

    # Authenticated request
    me_res = auth_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "me@careerlens.dev"
    assert me_res.json()["name"] == "Me User"
