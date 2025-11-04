resource "aws_dynamodb_table" "health_check_results" {
  name             = "WebsiteHealthCheckResults"
  billing_mode     = "PAY_PER_REQUEST" 
  hash_key         = "Timestamp"
  range_key        = "URL"

  attribute {
    name = "Timestamp"
    type = "S" 
  }

  attribute {
    name = "URL"
    type = "S"
  }

  tags = {
    Name = "HealthCheckResultsTable"
  }
}


resource "aws_iam_policy" "dynamodb_write_policy" {
  name        = "LambdaDynamoDBWritePolicy"
  description = "Allows the Lambda function to write items to the DynamoDB results table."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
        ]
        Resource = aws_dynamodb_table.health_check_results.arn
      },
    ]
  })
}


resource "aws_iam_role_policy_attachment" "dynamodb_write_attach" {
  role       = aws_iam_role.health_check_lambda_role.name
  policy_arn = aws_iam_policy.dynamodb_write_policy.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health_check_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.five_min_schedule.arn
}
