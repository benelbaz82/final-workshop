import boto3
import requests
import time
import os
from botocore.exceptions import ClientError

# Configuration from environment variables
INSTANCE_ID = os.getenv('INSTANCE_ID')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
WHATSAPP_URL = os.getenv('WHATSAPP_URL', 'https://new-waha.goblindeals.org/')
INTERVAL = int(os.getenv('INTERVAL', 60))  # seconds for checking existence

# Status Page API Configuration
METRIC_ID = int(os.getenv('EC2_METRIC_ID', 2))  # Different metric ID for EC2
API_URL = os.getenv('API_URL', 'http://host.docker.internal:8000/api/metrics/metric-points/')
API_TOKEN = os.getenv('API_TOKEN', 'YOUR_API_TOKEN')
HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

# AWS credentials should be set via environment variables or IAM roles
ec2 = boto3.client('ec2', region_name=AWS_REGION)

def check_instance_exists(instance_id):
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        # Check if instance is running
        state = response['Reservations'][0]['Instances'][0]['State']['Name']
        return state == 'running'
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidInstanceId.NotFound':
            return False
        else:
            # Other error, re-raise
            raise

def send_metric_point(value):
    data = {
        "metric": METRIC_ID,
        "value": value
    }
    try:
        response = requests.post(API_URL, json=data, headers=HEADERS, timeout=10)
        if response.status_code == 201:
            print(f"Sent EC2 status: {value}")
        else:
            print(f"Error sending metric: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to send metric: {e}")

def send_whatsapp_notification(instance_id):
    data = {
        "message": f"EC2 instance {instance_id} has been deleted or stopped",
        "instance_id": instance_id
    }
    try:
        response = requests.post(WHATSAPP_URL, json=data, timeout=10)
        if response.status_code in [200, 201]:
            print(f"Sent WhatsApp notification for instance: {instance_id}")
        else:
            print(f"Failed to send WhatsApp notification: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to send WhatsApp notification: {e}")

if __name__ == "__main__":
    if not INSTANCE_ID:
        print("INSTANCE_ID environment variable is required")
        exit(1)

    print(f"Starting EC2 monitor for instance {INSTANCE_ID}...")
    last_exists = None
    while True:
        exists = check_instance_exists(INSTANCE_ID)
        if exists:
            # Send metric every second while running
            send_metric_point(1)  # 1 = running
            time.sleep(1)
        else:
            # Instance not running
            if last_exists is True:
                # Status changed from running to not running
                print(f"Instance {INSTANCE_ID} is no longer running")
                send_whatsapp_notification(INSTANCE_ID)
            # Send metric once when not running
            send_metric_point(0)  # 0 = not running
            time.sleep(INTERVAL)  # Check less frequently when not running
        last_exists = exists