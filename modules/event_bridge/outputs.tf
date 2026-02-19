output "event_rule" {
    description = "The name of the CloudWatch Event Rule that triggers the health check Lambda."
    value       = aws_cloudwatch_event_rule.five_min_schedule.arn
  
}
