resource "aws_sns_topic" "health_check_topic" {
  name = "WebsiteHealthCheckTopic"
}


resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.health_check_topic.arn
  protocol  = "email"
  endpoint  = var.email_endpoint
}