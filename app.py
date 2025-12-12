from flask import Flask, request, jsonify, render_template
import sqlite3, datetime

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect("alerts.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS alerts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric TEXT,
        value REAL,
        message TEXT,
        label TEXT,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()


@app.route("/alerts", methods=["POST"])
def receive_alert():
    data = request.get_json()
    metric = data.get("metric")
    value = data.get("value")
    message = data.get("message", "")
    
    label = "Critical" if metric == "CPU" and value >= 90 else "Noise"
    ts = datetime.datetime.utcnow().isoformat()

    conn = get_db()
    conn.execute(
        "INSERT INTO alerts(metric, value, message, label, timestamp) VALUES (?,?,?,?,?)",
        (metric, value, message, label, ts)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"}), 201


@app.route("/alerts", methods=["GET"])
def list_alerts():
    conn = get_db()
    rows = conn.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    return render_template("alerts.html", alerts=rows)

if __name__ == "__main__":
    init_db()     
    app.run(debug=True)
