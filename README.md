# Serverless Website Health Checker (AWS + Terraform)

This project deploys a serverless health-checking system on AWS using Terraform. It leverages an AWS Lambda function, triggered periodically by Amazon EventBridge (CloudWatch Events), to perform an HTTP health check on a specified URL. Notifications regarding the website's health are sent via an Amazon SNS Topic.

## Results

![Health check results](images/results.png)

## Logic

| Scenario | HTTP Code | Load Time | is_healthy | SNS Email Sent? |
|----------|-----------|-----------|-----------|-----------------|
| Perfect | 200 | 450ms | True | No |
| Slow Site | 200 | 3200ms | False | Yes |
| Broken Page | 404 | 100ms | False | Yes |
| Server Crash | None (Timeout) | N/A | False | Yes |