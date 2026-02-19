resource "aws_cloudwatch_event_rule" "five_min_schedule" {
  name                = "RunHealthCheckEvery5Minutes"
  description         = "Triggers the Lambda every 5 minutes"
  schedule_expression = "rate(5 minutes)"
}


resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.five_min_schedule.name
  arn       = var.checker_function_arn
  target_id = "HealthCheckLambdaTarget"
}


resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge2"
  action        = "lambda:InvokeFunction"
  function_name = var.checker_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.five_min_schedule.arn
}