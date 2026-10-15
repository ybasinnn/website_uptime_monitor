import json
import boto3
import os
import ssl
import socket
import time
import urllib.error
import urllib.request
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

class RedirectRecorder(urllib.request.HTTPRedirectHandler):
    """Follows redirects like urllib normally does, but records each hop's status code."""
    def __init__(self):
        self.history = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.history.append(code)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def http_get(url, timeout):
    """Returns (status_code, duration_ms, redirect_history) using only the standard library."""
    recorder = RedirectRecorder()
    opener = urllib.request.build_opener(recorder)
    request = urllib.request.Request(url, headers={'User-Agent': 'WebsiteHealthChecker/1.0'})

    start = time.perf_counter()
    try:
        with opener.open(request, timeout=timeout) as response:
            status_code = response.status
    except urllib.error.HTTPError as e:
        # Non-2xx responses still count as a response, not a connection failure
        status_code = e.code
        e.close()
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    return status_code, duration_ms, recorder.history

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
        status_code, duration_ms, history = http_get(url, timeout=10)

        redirected = len(history) > 0
        chain = " -> ".join([str(code) for code in history] + [str(status_code)])
        
        tls_version, ssl_days = get_ssl_details(url)
        
        # --- Health Checks ---
        if status_code != 200:
            is_healthy = False
            reasons.append(f"HTTP {status_code}")
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
        status_code, duration_ms, tls_version, ssl_days, redirected, chain = 0, 0, "N/A", 0, False, "Error"

    # 1. Always Save to DynamoDB
    save_result(url, status, status_code, duration_ms, tls_version, ssl_days, redirected, chain)
    
    # 2. ONLY send SNS if not healthy
    if not is_healthy:
        send_alert(url, status, status_code, reasons)
    
    return {'statusCode': 200, 'body': json.dumps({'is_healthy': is_healthy})}