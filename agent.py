import psutil, requests, time

BACKEND_URL = "http://127.0.0.1:5000/alerts"

while True:
    # Get current CPU usage
    cpu = psutil.cpu_percent()
    # Send alert if CPU usage is high
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
   # Wait before checking again 5 secon
    time.sleep(5) 
