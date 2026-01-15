import json
import requests
import boto3
import os
from datetime import datetime

# --- Configuration Constants ---
MAX_LOAD_TIME_MS = 2500
MAX_LOAD_TIME_SECONDS = MAX_LOAD_TIME_MS / 1000

# --- AWS Clients ---
sns_client = boto3.client('sns')
dynamodb_client = boto3.client('dynamodb')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
TARGET_URL = os.environ.get('TARGET_URL', "https://default-url.com")
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

def save_result(url: str, status: str, http_code: int, duration_ms: float):
    if not DYNAMODB_TABLE:
        return
    try:
        current_time = datetime.utcnow().isoformat()
        item = {
            'Timestamp': {'S': current_time},
            'URL': {'S': url},
            'Status': {'S': status},
            'HTTPStatusCode': {'N': str(http_code)},
            'DurationMs': {'N': str(duration_ms)},
        }
        dynamodb_client.put_item(TableName=DYNAMODB_TABLE, Item=item)
    except Exception as e:
        print(f"ERROR: DynamoDB save failed: {e}")

def lambda_handler(event, context):
    url = TARGET_URL
    lambda_http_status = 200
    http_code = 0
    request_duration_ms = 0.0
    status = "Unknown"
    is_healthy = True # Assume healthy until proven otherwise
    
    try:
        response = requests.get(url, timeout=10)
        request_duration_seconds = response.elapsed.total_seconds()
        request_duration_ms = round(request_duration_seconds * 1000, 2)
        http_code = response.status_code
        
        # 1. Check if status is NOT 200
        if http_code != 200:
            is_healthy = False
            status = f"Unhealthy - Status code: {http_code}"
            lambda_http_status = 502
        
        # 2. Check if it's slow (even if status is 200)
        elif request_duration_seconds > MAX_LOAD_TIME_SECONDS:
            is_healthy = False
            status = f"Unhealthy - Slow Load ({request_duration_ms}ms)"
            # Note: We keep lambda_http_status 200 because the site is technically up
            
        else:
            status = "Healthy"
            
    except Exception as e:
        is_healthy = False
        status = f"Critical Error: {str(e)}"
        http_code = 0
        lambda_http_status = 504

    # Save all attempts to DynamoDB for history
    save_result(url, status, http_code, request_duration_ms)

    # EMAIL LOGIC: Trigger if is_healthy is False
    if SNS_TOPIC_ARN and not is_healthy:
        print(f"ALERT: Sending email because site is {status}")
        subject = f"ALERT: Website {url} is {status}"
        message = (
            f"Website health check failed!\n"
            f"URL: {url}\n"
            f"Result: {status}\n"
            f"HTTP Code: {http_code}\n"
            f"Load Time: {request_duration_ms}ms"
        )
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )

        
    return {
        'statusCode': lambda_http_status,
        'body': json.dumps({
            'url': url,
            'status': status,
            'http_code': http_code,
            'duration_ms': request_duration_ms,
            'is_healthy': is_healthy
        })
    }
