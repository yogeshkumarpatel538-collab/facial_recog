def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_record_count_event(client, admin_headers, auth_headers):
    camera_response = client.post(
        "/api/v1/cameras",
        headers=admin_headers,
        json={
            "name": "Lobby Cam",
            "rtsp_url": "rtsp://192.168.1.11:554/stream1",
            "location": "Lobby",
            "active": True,
        },
    )
    camera_id = camera_response.json()["id"]

    event_response = client.post(
        "/api/v1/count-events",
        headers=auth_headers,
        json={
            "camera_id": camera_id,
            "track_id": "track-001",
            "direction": "in",
        },
    )
    assert event_response.status_code == 201
    event = event_response.json()
    assert event["direction"] == "in"
    assert event["track_id"] == "track-001"
