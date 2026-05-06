# AI Alert Filtering System

## Overview

This project is an AI-based alert filtering system built using Flask, SQLite, and Machine Learning.

The system receives alerts, extracts features, and classifies them as Critical or Noise using a Logistic Regression model.

## Features

- REST API (POST /alerts, GET /alerts)
- Feature extraction (time, message, value buckets)
- Machine learning classification (Logistic Regression)
- Rule-based fallback
- SQLite database storage
- Dashboard with charts and filters

## How to Run

### 1. Generate dataset

```bash
python generate_alerts.py
```
