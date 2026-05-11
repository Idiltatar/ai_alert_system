from ai_alert.app import app, init_db, is_low_confidence


def setup_module(module):
    init_db()


def test_post_valid_alert():
    client = app.test_client()

    response = client.post("/alerts", json={
        "metric": "CPU",
        "value": 95,
        "message": "test high cpu"
    })

    assert response.status_code == 201

    data = response.get_json()
    assert data["status"] == "ok"
    assert "id" in data
    assert "label" in data
    assert "label_source" in data
    assert "confidence" in data
    assert "explanation" in data
    assert 0 <= data["confidence"] <= 100
    assert data["explanation"]


def test_post_invalid_alert():
    client = app.test_client()

    response = client.post("/alerts", json={
        "metric": "",
        "value": None
    })

    assert response.status_code == 400

    data = response.get_json()
    assert data["status"] == "error"
    assert "message" in data


def test_low_confidence_helper():
    assert is_low_confidence(69.9) is True
    assert is_low_confidence(70.0) is False
    assert is_low_confidence(None) is False
