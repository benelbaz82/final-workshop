import psutil
import requests
import time
import os

# Set procfs path to monitor host CPU
psutil.PROCFS_PATH = '/host/proc'

# Configuration from environment variables
METRIC_ID = int(os.getenv('METRIC_ID', 1))
API_URL = os.getenv('API_URL', 'http://host.docker.internal:8000/api/metric-points/')
API_TOKEN = os.getenv('API_TOKEN', 'YOUR_API_TOKEN')
INTERVAL = int(os.getenv('INTERVAL', 60))  # seconds

HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

def get_cpu_usage():
    # To monitor host CPU, use /host/proc
    return psutil.cpu_percent(interval=1, percpu=False)

def send_metric_point(value):
    data = {
        "metric": METRIC_ID,
        "value": round(value, 2)
    }
    try:
        response = requests.post(API_URL, json=data, headers=HEADERS, timeout=10)
        if response.status_code == 201:
            print(f"Sent CPU usage: {value}%")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to send: {e}")

if __name__ == "__main__":
    print("Starting CPU monitor...")
    while True:
        cpu = get_cpu_usage()
        send_metric_point(cpu)
        time.sleep(INTERVAL)