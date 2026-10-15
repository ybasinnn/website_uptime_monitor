output "topic_arn" {
  description = "The ARN of the SNS topic for use in IAM policies"
  value       = aws_sns_topic.health_check_topic.arn
}
