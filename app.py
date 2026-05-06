from flask import Flask, request, jsonify, render_template, redirect
import sqlite3
import datetime
import joblib
import os

app = Flask(__name__)

DB_PATH = "alerts.db"
MODEL_PATH = "model.pkl"

model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        print("ML model loaded:", MODEL_PATH)
    except Exception as e:
        model = None
        print("Failed to load model.pkl:", e)
else:
    print(" model.pkl not found yet. Run train_model.py first.")


@app.route("/")
def home():
    return redirect("/alerts")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_column(conn, table_name, column_name, column_def):
    cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table_name});").fetchall()]
    if column_name not in cols:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def};")
        conn.commit()
        print(f"Added missing column: {table_name}.{column_name}")


def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS alerts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric TEXT NOT NULL,
        value REAL NOT NULL,
        message TEXT,
        label TEXT,
        label_source TEXT,
        timestamp TEXT,
        hour INTEGER,
        day_of_week INTEGER,
        is_weekend INTEGER,
        message_len INTEGER,
        value_bucket TEXT
    )
    """)
    conn.commit()
    ensure_column(conn, "alerts", "label_source", "TEXT")
    conn.close()


def extract_features(ts_dt, value, message):
    hour = ts_dt.hour
    day_of_week = ts_dt.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0
    message_len = len(message or "")

    if value is None:
        value_bucket = "unknown"
    elif value < 50:
        value_bucket = "low"
    elif value < 80:
        value_bucket = "medium"
    else:
        value_bucket = "high"

    return hour, day_of_week, is_weekend, message_len, value_bucket


def validate_payload(data):
    if not isinstance(data, dict):
        raise ValueError("JSON body must be an object.")

    metric = data.get("metric", None)
    value = data.get("value", None)
    message = data.get("message", "")

    if metric is None or str(metric).strip() == "":
        raise ValueError("Missing or empty field: 'metric'.")

    if value is None:
        raise ValueError("Missing field: 'value'.")

    try:
        value = float(value)
    except Exception:
        raise ValueError("Field 'value' must be a number.")

    return str(metric).strip(), value, str(message)


def baseline_classifier(metric, value, message):
    msg = (message or "").lower()
    m = (metric or "").upper()

    critical_keywords = ["failed", "error", "panic", "outage", "down", "unreachable", "disk full"]
    if any(k in msg for k in critical_keywords):
        return "Critical"

    if m == "CPU" and value >= 90:
        return "Critical"
    if m in ["MEMORY", "RAM"] and value >= 90:
        return "Critical"
    if m == "DISK" and value >= 95:
        return "Critical"

    return "Noise"


def predict_label(metric, value, message, hour, day_of_week, is_weekend, message_len, value_bucket):
    if model is None:
        raise RuntimeError("ML model is not loaded. Run train_model.py first.")

    X = [{
        "metric": metric,
        "value": value,
        "message": message,
        "hour": hour,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "message_len": message_len,
        "value_bucket": value_bucket
    }]

    pred = model.predict(X)[0]

    if isinstance(pred, str):
        return pred, "ml"

    label = "Critical" if int(pred) == 1 else "Noise"
    return label, "ml"


@app.route("/alerts", methods=["POST"])
def receive_alert():
    data = request.get_json(silent=True) or {}

    try:
        metric, value, message = validate_payload(data)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    ts_dt = datetime.datetime.now(datetime.UTC)
    ts = ts_dt.isoformat()

    hour, day_of_week, is_weekend, message_len, value_bucket = extract_features(ts_dt, value, message)

    try:
        label, label_source = predict_label(
            metric, value, message, hour, day_of_week, is_weekend, message_len, value_bucket
        )
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"ML prediction failed: {str(e)}"
        }), 500

    conn = get_db()
    ensure_column(conn, "alerts", "label_source", "TEXT")

    cur = conn.execute(
        """INSERT INTO alerts(metric, value, message, label, label_source, timestamp,
                              hour, day_of_week, is_weekend, message_len, value_bucket)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (metric, value, message, label, label_source, ts,
         hour, day_of_week, is_weekend, message_len, value_bucket)
    )
    conn.commit()
    alert_id = cur.lastrowid
    conn.close()

    return jsonify({
        "status": "ok",
        "id": alert_id,
        "label": label,
        "label_source": label_source,
        "features": {
            "hour": hour,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "message_len": message_len,
            "value_bucket": value_bucket
        }
    }), 201


@app.route("/alerts", methods=["GET"])
def list_alerts():
    conn = get_db()
    ensure_column(conn, "alerts", "label_source", "TEXT")

    label_filter = request.args.get("label", "all")
    metric_filter = request.args.get("metric", "all")
    q = (request.args.get("q", "") or "").strip()

    where = []
    params = []

    if label_filter != "all":
        where.append("label = ?")
        params.append(label_filter)

    if metric_filter != "all":
        where.append("metric = ?")
        params.append(metric_filter)

    if q:
        where.append("message LIKE ?")
        params.append(f"%{q}%")

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    rows = conn.execute(
        f"SELECT * FROM alerts {where_sql} ORDER BY id DESC LIMIT 200",
        params
    ).fetchall()

    total = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    critical = conn.execute("SELECT COUNT(*) FROM alerts WHERE label='Critical'").fetchone()[0]
    noise = conn.execute("SELECT COUNT(*) FROM alerts WHERE label='Noise'").fetchone()[0]

    metrics = [r[0] for r in conn.execute("SELECT DISTINCT metric FROM alerts ORDER BY metric").fetchall()]

    conn.close()

    return render_template(
        "alerts.html",
        alerts=rows,
        total=total,
        critical=critical,
        noise=noise,
        metrics=metrics,
        label_filter=label_filter,
        metric_filter=metric_filter,
        q=q
    )


@app.route("/alerts/summary", methods=["GET"])
def alerts_summary():
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    critical = conn.execute("SELECT COUNT(*) FROM alerts WHERE label='Critical'").fetchone()[0]
    noise = conn.execute("SELECT COUNT(*) FROM alerts WHERE label='Noise'").fetchone()[0]

    per_day_rows = conn.execute("""
        SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS count
        FROM alerts
        GROUP BY day
        ORDER BY day DESC
        LIMIT 14
    """).fetchall()

    per_metric_rows = conn.execute("""
        SELECT metric, COUNT(*) AS count
        FROM alerts
        GROUP BY metric
        ORDER BY count DESC
        LIMIT 6
    """).fetchall()

    conn.close()

    per_day = [{"day": r["day"], "count": r["count"]} for r in reversed(per_day_rows)]
    per_metric = [{"metric": r["metric"], "count": r["count"]} for r in per_metric_rows]

    return jsonify({
        "total": total,
        "critical": critical,
        "noise": noise,
        "per_day": per_day,
        "per_metric": per_metric
    })


@app.route("/alerts/<int:alert_id>/label", methods=["POST"])
def update_label(alert_id):
    data = request.get_json(silent=True) or {}
    new_label = str(data.get("label", "")).strip()

    if new_label not in ["Critical", "Noise"]:
        return jsonify({"status": "error", "message": "label must be 'Critical' or 'Noise'"}), 400

    conn = get_db()
    ensure_column(conn, "alerts", "label_source", "TEXT")

    cur = conn.execute(
        "UPDATE alerts SET label=?, label_source=? WHERE id=?",
        (new_label, "manual", alert_id)
    )
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        return jsonify({"status": "error", "message": "Alert not found"}), 404

    return jsonify({
        "status": "ok",
        "id": alert_id,
        "label": new_label,
        "label_source": "manual"
    }), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True)