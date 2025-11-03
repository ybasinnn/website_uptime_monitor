import json
import requests
import boto3
import os
from datetime import datetime

sns_client = boto3.client('sns')
dynamodb_client = boto3.client('dynamodb')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
TARGET_URL = os.environ.get('TARGET_URL', "https://default-url.com")
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

def save_result(url, status, http_code):
    """Saves the health check result to the DynamoDB table."""
    try:
        current_time = datetime.utcnow().isoformat()
        
        item = {
            'Timestamp': {'S': current_time},
            'URL': {'S': url},
            'Status': {'S': status},
            'HTTPStatusCode': {'N': str(http_code)},
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
    
    # Initialize the Lambda HTTP status code and the actual HTTP status
    lambda_http_status = 200
    http_code = 0
    
    try:
        response = requests.get(url, timeout=10)
        http_code = response.status_code
        
        if http_code == 200:
            status = "Healthy"
            subject = f"SUCCESS: Website {url} is Healthy"
            message = f"Website {url} returned status code 200 (Healthy)."
            # Status code remains 200
        else:
            status = f"Unhealthy - Status code: {http_code}"
            subject = f"ALERT: Website {url} is UNHEALTHY"
            message = f"Website {url} returned status code {http_code} (Unhealthy)."
            lambda_http_status = 502 # Bad Gateway
            
    except requests.exceptions.RequestException as e:
        # Handle exceptions like DNS failure, connection timeout, etc.
        status = f"Unhealthy - Exception: {str(e.__class__.__name__)}"
        subject = f"ALERT: Website {url} is UNHEALTHY (Exception)"
        message = f"Website {url} check failed with exception: {str(e)}"
        lambda_http_status = 504 # Gateway Timeout
    
    print(f"Website {url} status: {status}, HTTP Code: {http_code}")
    
    # 1. Log result to DynamoDB
    if DYNAMODB_TABLE:
        save_result(url, status, http_code)
    
    # 2. Send Notification via SNS
    if SNS_TOPIC_ARN:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    
    # 3. Return the dynamic status code
    return {
        'statusCode': lambda_http_status,
        'body': json.dumps({
            'url': url,
            'status': status,
            'http_code': http_code
        })
    }
