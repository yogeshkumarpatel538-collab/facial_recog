TEST_PASSWORD = "SecurePass1"


def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": TEST_PASSWORD},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "viewer"


def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": TEST_PASSWORD}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["error_code"] == "CONFLICT"


def test_register_weak_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "weakpass"},
    )
    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"


def test_login_success(client, viewer_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": viewer_user.email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, viewer_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": viewer_user.email, "password": "WrongPass1"},
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "AUTHENTICATION_FAILED"


def test_get_me(client, auth_headers, viewer_user):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == viewer_user.email
    assert data["role"] == "viewer"


def test_get_me_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_refresh_tokens(client, viewer_user):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": viewer_user.email, "password": TEST_PASSWORD},
    )
    refresh_token = login.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["refresh_token"] != refresh_token


def test_logout_revokes_refresh_token(client, viewer_user):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": viewer_user.email, "password": TEST_PASSWORD},
    )
    refresh_token = login.json()["refresh_token"]

    logout = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout.status_code == 200

    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh.status_code == 401


def test_viewer_cannot_create_camera(client, auth_headers):
    response = client.post(
        "/api/v1/cameras",
        headers=auth_headers,
        json={
            "name": "Cam 1",
            "rtsp_url": "rtsp://localhost/stream",
            "location": "Lobby",
            "active": True,
        },
    )
    assert response.status_code == 403
    assert response.json()["error_code"] == "AUTHORIZATION_FAILED"


def test_admin_can_create_camera(client, admin_headers):
    response = client.post(
        "/api/v1/cameras",
        headers=admin_headers,
        json={
            "name": "Admin Cam",
            "rtsp_url": "rtsp://localhost/stream",
            "location": "Lobby",
            "active": True,
        },
    )
    assert response.status_code == 201


def test_protected_route_requires_auth(client):
    response = client.get("/api/v1/cameras")
    assert response.status_code == 401
