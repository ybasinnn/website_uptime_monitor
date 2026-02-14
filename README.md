# Serverless Website Health Checker (AWS + Terraform)

This project deploys a serverless health-monitoring system on AWS using Terraform. It leverages an AWS Lambda function, triggered every 5 minutes by Amazon EventBridge (CloudWatch Events), to perform an HTTP health check on a specified URL. 

Notifications regarding the website's status are sent via an Amazon SNS Topic. Execution results are persisted in an Amazon DynamoDB table, which are then retrieved by a secondary Lambda function to generate a status report hosted in an Amazon S3 bucket.

## Architecture
![Architecture](images/website_monitor_architecture.png)

## Workflow
1. **EventBridge**: Triggers the "Checker" Lambda function on a 5-minute schedule.
2. **Lambda (Checker)**: Executes an HTTP request and evaluates the response.
3. **SNS**: Dispatches alerts if the health check fails or the site is unreachable.
4. **DynamoDB**: Stores historical check data (status codes, timestamps, and latency).
5. **Lambda (Reporter)**: Queries DynamoDB to aggregate uptime data.
6. **S3 Bucket**: Hosts the final output for visualization.

## Results
![Health check results](images/results.png)

## Deployment
1. Initialize Terraform: `terraform init`
2. Review the plan: `terraform plan`
3. Deploy the infrastructure: `terraform apply`