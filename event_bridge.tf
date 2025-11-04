## EventBridge 
resource "aws_cloudwatch_event_rule" "five_min_schedule" {
  name                = "RunHealthCheckEvery5Minutes"
  description         = "Triggers the Lambda every 5 minutes"
  schedule_expression = "rate(5 minutes)"
}

# Set the Lambda function as the target of the rule
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.five_min_schedule.name
  arn       = aws_lambda_function.health_check_lambda.arn
  target_id = "HealthCheckLambdaTarget"
}

# Grant EventBridge permission to invoke the Lambda function
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge2"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health_check_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.five_min_schedule.arn
}