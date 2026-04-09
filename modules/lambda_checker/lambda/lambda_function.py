import json
import requests
import boto3
import os
import ssl
import socket
from datetime import datetime
from urllib.parse import urlparse

# --- Configuration ---
MAX_LOAD_TIME_MS = 2500
MAX_LOAD_TIME_SECONDS = MAX_LOAD_TIME_MS / 1000

sns_client = boto3.client('sns')
dynamodb_client = boto3.client('dynamodb')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
TARGET_URL = os.environ.get('TARGET_URL', "https://default-url.com")
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

def get_ssl_details(url):
    """Fetches TLS version and certificate expiry with SNI support."""
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE 

    try:
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert(binary_form=True)
                tls_version = ssock.version()
                
                context_v = ssl.create_default_context()
                with socket.create_connection((hostname, 443), timeout=5) as sock2:
                    with context_v.wrap_socket(sock2, server_hostname=hostname) as ssock2:
                        readable_cert = ssock2.getpeercert()
                        expire_date_str = readable_cert['notAfter']
                        expire_date = datetime.strptime(expire_date_str, '%b %d %H:%M:%S %Y %Z')
                        days_left = (expire_date - datetime.utcnow()).days
                        return tls_version, days_left
    except Exception as e:
        print(f"SSL Detail Error: {e}")
        return "TLSv1.2+", 0 

def save_result(url, status, http_code, duration_ms, tls_ver, ssl_days, redirected, chain):
    if not DYNAMODB_TABLE: return
    try:
        item = {
            'Timestamp': {'S': datetime.utcnow().isoformat()},
            'URL': {'S': url},
            'Status': {'S': status},
            'HTTPStatusCode': {'N': str(http_code)},
            'DurationMs': {'N': str(duration_ms)},
            'TLSVersion': {'S': str(tls_ver)},
            'SSLDaysLeft': {'N': str(ssl_days)},
            'Redirected': {'BOOL': redirected},
            'RedirectChain': {'S': str(chain)}
        }
        dynamodb_client.put_item(TableName=DYNAMODB_TABLE, Item=item)
    except Exception as e:
        print(f"DynamoDB Error: {e}")

def send_alert(url, status, code, reasons):
    """Sends notification via SNS."""
    if not SNS_TOPIC_ARN:
        return
    
    subject = f"🚨 ALERT: {url} is Unhealthy"
    message = (
        f"Health Check Failed!\n\n"
        f"URL: {url}\n"
        f"Status: {status}\n"
        f"HTTP Code: {code}\n"
        f"Reasons: {', '.join(reasons)}\n"
        f"Timestamp: {datetime.utcnow().isoformat()}"
    )
    
    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except Exception as e:
        print(f"SNS Error: {e}")

def lambda_handler(event, context):
    url = TARGET_URL
    is_healthy = True
    reasons = []
    
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        duration_ms = round(response.elapsed.total_seconds() * 1000, 2)
        
        redirected = len(response.history) > 0
        chain = " -> ".join([str(r.status_code) for r in response.history] + [str(response.status_code)])
        
        tls_version, ssl_days = get_ssl_details(url)
        
        # --- Health Checks ---
        if response.status_code != 200:
            is_healthy = False
            reasons.append(f"HTTP {response.status_code}")
        if (duration_ms / 1000) > MAX_LOAD_TIME_SECONDS:
            is_healthy = False
            reasons.append(f"Slow response ({duration_ms}ms)")
        if ssl_days < 14:
            is_healthy = False
            reasons.append(f"SSL expiring in {ssl_days} days")

        status = "Healthy" if is_healthy else "Unhealthy"
            
    except Exception as e:
        is_healthy = False
        reasons.append(type(e).__name__)
        status = "Unhealthy"
        response, duration_ms, tls_version, ssl_days, redirected, chain = type('obj', (object,), {'status_code': 0}), 0, "N/A", 0, False, "Error"

    # 1. Always Save to DynamoDB
    save_result(url, status, response.status_code, duration_ms, tls_version, ssl_days, redirected, chain)
    
    # 2. ONLY send SNS if not healthy
    if not is_healthy:
        send_alert(url, status, response.status_code, reasons)
    
    return {'statusCode': 200, 'body': json.dumps({'is_healthy': is_healthy})}