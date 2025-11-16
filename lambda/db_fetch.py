import json
import boto3
import os
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb')

# Retrieve the DynamoDB table name from environment variables
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

def lambda_handler(event, context):
    """
    Scans the DynamoDB table for health check results and returns them.
    """
    if not DYNAMODB_TABLE:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'DYNAMODB_TABLE environment variable not set.'}),
            'headers': {'Access-Control-Allow-Origin': '*'}
        }

    try:
        # Scan operation to retrieve a limited number of items.
        # NOTE: For high-volume data, a Query operation is generally more efficient.
        response = dynamodb.scan(
            TableName=DYNAMODB_TABLE,
            Limit=20  # Limit to the 20 most recent checks for the dashboard
        )

        items = []
        for item in response.get('Items', []):
            # Deserialize the DynamoDB item structure (e.g., {'S': 'value'} -> 'value')
            items.append({
                'Timestamp': item.get('Timestamp', {}).get('S', 'N/A'),
                'DurationMs': item.get('DurationMs', {}).get('N', '0'),
                'URL': item.get('URL', {}).get('S', 'N/A'),
                'Status': item.get('Status', {}).get('S', 'N/A'),
                'HTTPStatusCode': item.get('HTTPStatusCode', {}).get('N', '0')
            })

        # Sort items by Timestamp descending to show the latest first
        sorted_items = sorted(items, key=lambda x: x['Timestamp'], reverse=True)

        return {
            'statusCode': 200,
            'body': json.dumps(sorted_items),
            # CRITICAL: Allow CORS for the S3 static site to access the API
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*' 
            }
        }

    except ClientError as e:
        error_message = e.response['Error']['Message']
        print(f"DynamoDB Client Error: {error_message}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'DynamoDB Error: {error_message}'}),
            'headers': {'Access-Control-Allow-Origin': '*'}
        }
    except Exception as e:
        print(f"General Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Server Error: {str(e)}'}),
            'headers': {'Access-Control-Allow-Origin': '*'}
        }