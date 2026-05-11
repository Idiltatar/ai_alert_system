from ai_alert.app import app, init_db


def setup_module(module):
    init_db()


def test_ml_label_source_is_ml():
    client = app.test_client()

    response = client.post("/alerts", json={
        "metric": "CPU",
        "value": 95,
        "message": "CPU usage critical"
    })

    assert response.status_code == 201

    data = response.get_json()

    assert data["label_source"] == "ml"
    assert data["label"] in ["Critical", "Noise"]
    assert 0 <= data["confidence"] <= 100
    assert "Prediction confidence" in data["explanation"]


def test_manual_update_changes_to_manual():
    client = app.test_client()

    response = client.post("/alerts", json={
        "metric": "DISK",
        "value": 97,
        "message": "Disk full"
    })

    assert response.status_code == 201

    alert_id = response.get_json()["id"]

    update_response = client.post(f"/alerts/{alert_id}/label", json={
        "label": "Noise"
    })

    assert update_response.status_code == 200

    updated = update_response.get_json()

    assert updated["label_source"] == "manual"
    assert updated["label"] == "Noise"


def test_needs_review_filter_loads_dashboard():
    client = app.test_client()

    response = client.get("/alerts?review=needs_review")

    assert response.status_code == 200
    assert b"Needs Review" in response.data
