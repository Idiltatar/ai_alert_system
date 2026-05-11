# AI Alert Filtering System

## Overview

This project is an AI-based alert filtering system built using Flask, SQLite, and Machine Learning.

The system receives alerts, extracts features, and classifies them as Critical or Noise using a Logistic Regression model.

## Features

- REST API (POST /alerts, GET /alerts)
- Feature extraction (time, message, value buckets)
- Machine learning classification (Logistic Regression)
- Explainable AI output for each prediction
- Confidence score for Critical/Noise classifications
- Low-confidence review queue for human-in-the-loop checking
- Rule-based fallback
- SQLite database storage
- Dashboard with charts and filters

## Explainable AI and Review Workflow

The system uses the model's prediction probabilities to calculate a confidence score for each alert. If the model predicts `Critical`, the confidence is the probability assigned to `Critical`; if it predicts `Noise`, the confidence is the probability assigned to `Noise`.

Alerts with ML confidence below `70%` are flagged as `Needs Review`. This adds a human-in-the-loop workflow where uncertain predictions can be checked manually instead of being trusted blindly. Each prediction also includes a short explanation based on the alert metric, value bucket, message keywords, timing features, predicted label, and confidence score.

## How to Run

### 1. Generate dataset

```bash
python -m ai_alert.generate_alerts
```
