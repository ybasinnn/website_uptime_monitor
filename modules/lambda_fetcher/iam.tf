resource "aws_iam_role" "dashboard_lambda_role" {
  name = "DashboardDataFetcherRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "dashboard_lambda_policy" {
  name        = "DashboardLambdaReadPolicy"
  description = "Allows the Dashboard Lambda to read from DynamoDB and log to CloudWatch."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # DynamoDB Read-Only Access (Scan)
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Scan"
        ]
        Resource = var.dynamodb_table_name_arn
      },
      # Standard CloudWatch Logging
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:*:*:log-group:/aws/lambda/${aws_lambda_function.dashboard_lambda.function_name}",
          "arn:aws:logs:*:*:log-group:/aws/lambda/${aws_lambda_function.dashboard_lambda.function_name}:*",
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "dashboard_lambda_policy_attach" {
  role       = aws_iam_role.dashboard_lambda_role.name
  policy_arn = aws_iam_policy.dashboard_lambda_policy.arn
}
