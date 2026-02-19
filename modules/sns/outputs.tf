output "topic_arn" {
  description = "The ARN of the SNS topic for use in IAM policies"
  value       = aws_sns_topic.health_check_topic.arn
}

output "email_endpoint_subscription" {
  description = "The email endpoint subscribed to the SNS topic for notifications."
  value       = aws_sns_topic_subscription.email_subscription.endpoint
}