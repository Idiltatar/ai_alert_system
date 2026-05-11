import psutil, requests, time

BACKEND_URL = "http://127.0.0.1:5000/alerts"

while True:
    cpu = psutil.cpu_percent()
    print("Current CPU Usage:", cpu)
    if cpu > 80:
        alert = {
            "metric": "CPU",
            "value": cpu,
            "message": "High CPU usage detected"
        }
        try:
            requests.post(BACKEND_URL, json=alert, timeout=3)
        except Exception as e:
            print("Failed to send alert:", e)
  
    time.sleep(5)
