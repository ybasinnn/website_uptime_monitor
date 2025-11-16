output "dashboard_s3_endpoint" {
  description = "The publicly accessible URL of the Static Website Dashboard."
  value       = aws_s3_bucket_website_configuration.website_config.website_endpoint
}


output "dashboard_api_url" {
  description = "The API Gateway URL used by the dashboard to fetch data."
  value       = local.api_url
}


output "dynamodb_table_name" {
  description = "The name of the DynamoDB table storing health check results."
  value       = aws_dynamodb_table.health_check_results.name
}