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
    
    # Create a context that ignores cert validation errors JUST for the check
    # if standard validation fails, but tries to get the cert regardless.
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE 

    try:
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Get the certificate in dict format
                cert = ssock.getpeercert(binary_form=True)
                tls_version = ssock.version()
                
                # Convert binary cert to dict to get 'notAfter'
                decoded_cert = ssl.DER_cert_to_PEM_cert(cert)
                # We use a fallback logic here to get dates if getpeercert() is empty
                # Using the ssock.getpeercert() without binary_form first:
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
        return "TLSv1.2+", 0 # Fallback values

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

def lambda_handler(event, context):
    url = TARGET_URL
    is_healthy = True
    
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        duration_ms = round(response.elapsed.total_seconds() * 1000, 2)
        
        redirected = len(response.history) > 0
        chain = " -> ".join([str(r.status_code) for r in response.history] + [str(response.status_code)])
        
        tls_version, ssl_days = get_ssl_details(url)
        
        reasons = []
        if response.status_code != 200:
            is_healthy = False
            reasons.append(f"Status {response.status_code}")
        if (duration_ms / 1000) > MAX_LOAD_TIME_SECONDS:
            is_healthy = False
            reasons.append("Slow")
        if ssl_days < 14 and tls_version != "Unknown":
            is_healthy = False
            reasons.append(f"SSL Expiring")

        status = "Healthy" if is_healthy else "Unhealthy: " + ", ".join(reasons)
            
    except Exception as e:
        is_healthy = False
        status = f"Unhealthy: {type(e).__name__}"
        response, duration_ms, tls_version, ssl_days, redirected, chain = type('obj', (object,), {'status_code': 0}), 0, "N/A", 0, False, "Error"

    save_result(url, status, response.status_code, duration_ms, tls_version, ssl_days, redirected, chain)
    
    return {'statusCode': 200, 'body': json.dumps({'is_healthy': is_healthy})}