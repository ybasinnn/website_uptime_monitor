import json
import requests
import boto3
import os
from datetime import datetime

# --- Configuration Constants ---
# Maximum acceptable load time in milliseconds
MAX_LOAD_TIME_MS = 2500
MAX_LOAD_TIME_SECONDS = MAX_LOAD_TIME_MS / 1000

# --- AWS Clients and Environment Variables ---
# Clients are initialized outside the handler for better performance (Lambda best practice)
sns_client = boto3.client('sns')
dynamodb_client = boto3.client('dynamodb')

# Environment variables
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
TARGET_URL = os.environ.get('TARGET_URL', "https://default-url.com")
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

def save_result(url: str, status: str, http_code: int, duration_ms: float):
    """
    Saves the comprehensive health check result, including duration, to the DynamoDB table.
    """
    if not DYNAMODB_TABLE:
        print("INFO: DYNAMODB_TABLE environment variable is not set. Skipping DynamoDB logging.")
        return

    try:
        current_time = datetime.utcnow().isoformat()
        
        item = {
            'Timestamp': {'S': current_time},
            'URL': {'S': url},
            'Status': {'S': status},
            'HTTPStatusCode': {'N': str(http_code)},
            'DurationMs': {'N': str(duration_ms)}, # Store the duration in milliseconds
        }
        
        dynamodb_client.put_item(
            TableName=DYNAMODB_TABLE,
            Item=item
        )
        print(f"Successfully logged result to DynamoDB at {current_time}")
    except Exception as e:
        # Log the error, but don't fail the whole Lambda execution
        print(f"ERROR: Could not save result to DynamoDB: {e}")


def lambda_handler(event, context):
    url = TARGET_URL
    
    # Initialize variables
    lambda_http_status = 200
    http_code = 0
    request_duration_ms = 0.0
    status = "Unknown"
    is_healthy = True
    
    try:
        # Perform the request and measure time
        response = requests.get(url, timeout=10)
        
        # Calculate duration from the response object
        request_duration_seconds = response.elapsed.total_seconds()
        request_duration_ms = round(request_duration_seconds * 1000, 2)
        http_code = response.status_code
        
        # --- Health Check Criteria ---
        
        # 1. Check HTTP Status Code
        if http_code != 200:
            is_healthy = False
            status = f"Unhealthy - Status code: {http_code}"
            lambda_http_status = 502 # Bad Gateway for unexpected response
        
        # 2. Check Load Time (only if status code was 200)
        elif request_duration_seconds > MAX_LOAD_TIME_SECONDS:
            is_healthy = False
            status = f"Unhealthy - Slow Load ({request_duration_ms:.2f}ms)"
            # Keep lambda_http_status 200 since the request succeeded, but we still alert
        
        # If both checks pass
        else:
            status = "Healthy"
            is_healthy = True
            
    except requests.exceptions.RequestException as e:
        # Handle exceptions like DNS failure, connection timeout, etc.
        is_healthy = False
        status = f"Unhealthy - Exception: {str(e.__class__.__name__)}"
        lambda_http_status = 504 # Gateway Timeout for connection issues

    # --- Notification and Logging ---

    # Determine subject and message based on final health status
    if is_healthy:
        subject = f"SUCCESS: Website {url} is Healthy"
        message = (
            f"Website {url} passed all checks.\n"
            f"HTTP Status: {http_code}\n"
            f"Load Time: {request_duration_ms:.2f} ms"
        )
    else:
        subject = f"ALERT: Website {url} is UNHEALTHY"
        message = (
            f"Website {url} check failed!\n"
            f"Status Reason: {status}\n"
            f"HTTP Status: {http_code}\n"
            f"Load Time: {request_duration_ms:.2f} ms (Threshold: {MAX_LOAD_TIME_MS} ms)"
        )
        
    print(f"Check result: Status='{status}', Code={http_code}, Duration={request_duration_ms:.2f}ms")
    
    # 1. Log result to DynamoDB
    save_result(url, status, http_code, request_duration_ms)
    
    # 2. Send Notification via SNS
    if SNS_TOPIC_ARN:
        print(f"Publishing message to SNS Topic: {SNS_TOPIC_ARN}")
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    else:
        print("INFO: SNS_TOPIC_ARN environment variable is not set. Skipping SNS notification.")
    
    # 3. Return the dynamic status code
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
