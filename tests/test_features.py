from generate_alerts import extract_features
import datetime


def test_value_bucket_high():
    ts = datetime.datetime.now()
    _, _, _, _, bucket = extract_features(ts, 95, "error")
    assert bucket == "high"


def test_value_bucket_medium():
    ts = datetime.datetime.now()
    _, _, _, _, bucket = extract_features(ts, 60, "normal")
    assert bucket == "medium"


def test_value_bucket_low():
    ts = datetime.datetime.now()
    _, _, _, _, bucket = extract_features(ts, 20, "ok")
    assert bucket == "low"


def test_weekend_flag():
    ts = datetime.datetime(2024, 6, 22)  # Saturday
    _, _, is_weekend, _, _ = extract_features(ts, 50, "msg")
    assert is_weekend == 1


def test_message_length():
    ts = datetime.datetime.now()
    _, _, _, message_len, _ = extract_features(ts, 50, "hello")
    assert message_len == 5