import sqlite3
import datetime
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "alerts.db"


# Create extra features for ML training
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

# Connect to SQLite database
def connect():
    return sqlite3.connect(DB_PATH)

# Create alerts table if this is a fresh deployment
def init_db(conn):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS alerts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric TEXT NOT NULL,
        value REAL NOT NULL,
        message TEXT,
        label TEXT,
        label_source TEXT,
        confidence REAL,
        explanation TEXT,
        timestamp TEXT,
        hour INTEGER,
        day_of_week INTEGER,
        is_weekend INTEGER,
        message_len INTEGER,
        value_bucket TEXT
    )
    """)
    conn.commit()

# Remove old alerts before generating new data
def clear_alerts_table(conn):
    conn.execute("DELETE FROM alerts;")
    conn.execute("DELETE FROM sqlite_sequence WHERE name='alerts';")
    conn.commit()

# Insert alert into database
def insert_alert(conn, metric, value, message, label, ts_dt):
    ts = ts_dt.isoformat()

    hour, day_of_week, is_weekend, message_len, value_bucket = extract_features(ts_dt, value, message)

    conn.execute(
        """INSERT INTO alerts(metric, value, message, label, timestamp,
                              hour, day_of_week, is_weekend, message_len, value_bucket)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (metric, float(value), message, label, ts,
         hour, day_of_week, is_weekend, message_len, value_bucket)
    )

# Generate low-risk sample alerts
def make_noise_alert(ts_dt):
    choices = [
        ("CPU", random.uniform(5, 65), "CPU usage normal"),
        ("MEMORY", random.uniform(10, 70), "Memory usage stable"),
        ("DISK", random.uniform(20, 75), "Disk usage within threshold"),
        ("NETWORK", random.uniform(1, 60), "Network traffic normal"),
    ]
    metric, value, msg = random.choice(choices)
    return metric, value, msg, "Noise"

# Generate critical sample alerts
def make_critical_alert(ts_dt):
    choices = [
        ("CPU", random.uniform(85, 100), "High CPU usage detected"),
        ("MEMORY", random.uniform(85, 100), "Memory pressure warning: possible leak"),
        ("DISK", random.uniform(90, 100), "Disk nearly full - write error risk"),
        ("NETWORK", random.uniform(85, 100), "Network outage suspected: unreachable"),
    ]
    metric, value, msg = random.choice(choices)

    if random.random() < 0.35:
        msg += " - error detected"
    if random.random() < 0.20:
        msg += " - service down"

    return metric, value, msg, "Critical"


def main():
    random.seed(42)
    conn = connect()

    init_db(conn)

    # Reset alerts table
    clear_alerts_table(conn)
    print("Cleared existing alerts from alerts.db")

    now = datetime.datetime.now(datetime.UTC)

    alerts = []

    # Generate noise alerts
    for _ in range(75):
        ts_dt = now - datetime.timedelta(days=random.randint(0, 13))
        ts_dt = ts_dt.replace(hour=random.randint(0, 23),
                              minute=random.randint(0, 59),
                              second=0, microsecond=0)
        alerts.append(make_noise_alert(ts_dt) + (ts_dt,))
    
    # Generate critical alerts
    for _ in range(75):
        ts_dt = now - datetime.timedelta(days=random.randint(0, 13))
        ts_dt = ts_dt.replace(hour=random.randint(0, 23),
                              minute=random.randint(0, 59),
                              second=0, microsecond=0)
        alerts.append(make_critical_alert(ts_dt) + (ts_dt,))
        
    # Shuffle dataset before inserting
    random.shuffle(alerts)

    for metric, value, message, label, ts_dt in alerts:
        insert_alert(conn, metric, value, message, label, ts_dt)

    conn.commit()

    cur = conn.execute("SELECT COUNT(*) FROM alerts;")
    total = cur.fetchone()[0]

    cur = conn.execute("SELECT label, COUNT(*) FROM alerts GROUP BY label;")
    by_label = cur.fetchall()

    conn.close()

    print("Inserted dataset into alerts.db")
    print("Total rows:", total)
    print("By label:", by_label)


if __name__ == "__main__":
    main()
