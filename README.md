# AlertIQ

## Overview

AlertIQ is an AI-powered alert classification platform built with Flask, SQLite and machine learning.

The system receives monitoring alerts, extracts engineered features, and classifies each alert as either `Critical` or `Noise`. It also shows a confidence score, an AI explanation, and a `Needs Review` status for low-confidence predictions.

This project is designed to reduce manual alert review and help teams prioritise incidents more effectively.

## Tech Stack

- Python
- Flask
- SQLite
- scikit-learn
- pandas
- psutil
- pytest

## Features

- REST API for receiving and displaying alerts
- Python monitoring agent using `psutil`
- Feature extraction for alert context
- Logistic Regression model for alert classification
- Confidence score for each machine learning prediction
- Explainable AI text for each classified alert
- Low-confidence `Needs Review` workflow
- Rule-based fallback logic
- SQLite database storage
- Flask dashboard with charts, filters and search

## Machine Learning

AlertIQ uses a Logistic Regression model trained on engineered alert features such as metric type, alert value, time context, message length and value bucket. In the project dataset, the model achieved strong classification performance during local evaluation.

## Project Structure

```text
ai_alert/
  app.py              Flask API and dashboard
  agent.py            Local monitoring agent
  generate_alerts.py  Generates sample alert data
  train_model.py      Trains the machine learning model

templates/
  alerts.html         Dashboard page

tests/                Unit and integration tests
alerts.db             SQLite alert database
model.pkl             Trained machine learning model
```

## How to Run the App

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install the dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate sample alert data

```bash
python -m ai_alert.generate_alerts
```

### 4. Train the machine learning model

```bash
python -m ai_alert.train_model
```

This creates the `model.pkl` file used by the Flask application.

### 5. Start the Flask app

```bash
python -m ai_alert.app
```

Open the dashboard in your browser:

```text
http://127.0.0.1:5000/alerts
```

## Optional: Run the Monitoring Agent

In a second terminal, activate the virtual environment again:

```bash
source venv/bin/activate
```

Then run the monitoring agent:

```bash
python -m ai_alert.agent
```

The agent checks local CPU usage with `psutil`. If CPU usage goes above the threshold, it sends an alert to the Flask API.

## How to Inject a Test Alert

Make sure the Flask app is running first:

```bash
python -m ai_alert.app
```

Then open a second terminal and send a test alert with `curl`.

### Inject a critical CPU alert

```bash
curl -X POST http://127.0.0.1:5000/alerts \
  -H "Content-Type: application/json" \
  -d '{"metric":"CPU","value":95,"message":"CPU usage critical"}'
```

### Inject a disk full alert

```bash
curl -X POST http://127.0.0.1:5000/alerts \
  -H "Content-Type: application/json" \
  -d '{"metric":"DISK","value":97,"message":"Disk full"}'
```

### Inject a low-confidence Needs Review example

Machine learning confidence depends on the trained model, so the easiest repeatable way to test the `Needs Review` dashboard filter is to insert one example directly into the database:

```bash
sqlite3 alerts.db "
INSERT INTO alerts (
  metric, value, message, label, label_source, confidence, explanation,
  timestamp, hour, day_of_week, is_weekend, message_len, value_bucket
)
VALUES (
  'CPU', 76, 'Ambiguous CPU alert for needs review test',
  'Critical', 'ml', 62.5,
  'CPU value is in the medium range. The model confidence is low, so this alert should be reviewed by a human.',
  datetime('now'), 12, 1, 0, 43, 'medium'
);
"
```

Then view the Needs Review filter:

```text
http://127.0.0.1:5000/alerts?review=needs_review
```

## API Endpoints

```text
GET  /alerts
POST /alerts
GET  /alerts/summary
POST /alerts/<alert_id>/label
```

## Run Tests

```bash
python -m pytest
```

## Notes

- `Critical` means the alert is likely to need attention.
- `Noise` means the alert is likely to be low priority or routine.
- `Needs Review` means the machine learning confidence is below `70%`.
- Manual label changes are saved with `label_source` set to `manual`.
