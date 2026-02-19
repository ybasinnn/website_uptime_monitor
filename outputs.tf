output "dashboard_s3_endpoint" {
  description = "Public S3 static website URL"
  value       = module.s3_fe.dashboard_s3_endpoint
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = module.dynamodb.table_name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = module.dynamodb.table_arn
}

output "api_gateway_endpoint" {
  description = "API Gateway invoke URL"
  value       = module.api_gw.api_endpoint
}
