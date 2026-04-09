import json
import boto3
import os

dynamodb = boto3.client('dynamodb')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

def lambda_handler(event, context):
    if not DYNAMODB_TABLE: return {'statusCode': 500, 'body': 'Table Error'}
    try:
        response = dynamodb.scan(TableName=DYNAMODB_TABLE, Limit=20)
        items = []
        for item in response.get('Items', []):
            items.append({
                'Timestamp': item.get('Timestamp', {}).get('S', 'N/A'),
                'DurationMs': item.get('DurationMs', {}).get('N', '0'),
                'URL': item.get('URL', {}).get('S', 'N/A'),
                'Status': item.get('Status', {}).get('S', 'N/A'),
                'HTTPStatusCode': item.get('HTTPStatusCode', {}).get('N', '0'),
                'TLS': item.get('TLSVersion', {}).get('S', 'N/A'),
                'SSLDays': item.get('SSLDaysLeft', {}).get('N', '0'),
                'Redirect': 'Yes' if item.get('Redirected', {}).get('BOOL') else 'No'
            })
        return {
            'statusCode': 200,
            'body': json.dumps(sorted(items, key=lambda x: x['Timestamp'], reverse=True)),
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
        }
    except Exception as e:
        return {'statusCode': 500, 'body': str(e), 'headers': {'Access-Control-Allow-Origin': '*'}}