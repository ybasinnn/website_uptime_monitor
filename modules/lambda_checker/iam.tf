resource "aws_iam_role" "health_check_lambda_role" {
  name = "HealthCheckLambdaExecutionRole"
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

resource "aws_iam_policy" "lambda_logging_policy" {
  name = "LambdaLoggingPolicy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
      ],
      Effect   = "Allow",
      Resource = "arn:aws:logs:*:*:*"
    }]
  })
}

# Policy allowing Lambda to publish to the SNS Topic
resource "aws_iam_policy" "sns_publish_policy" {
  name = "LambdaSNSPublishPolicy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action   = "sns:Publish",
      Effect   = "Allow",
      Resource = var.sns_topic_arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_log_attach" {
  role       = aws_iam_role.health_check_lambda_role.name
  policy_arn = aws_iam_policy.lambda_logging_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_sns_attach" {
  role       = aws_iam_role.health_check_lambda_role.name
  policy_arn = aws_iam_policy.sns_publish_policy.arn
}


resource "aws_iam_role_policy_attachment" "dynamodb_write_attach" {
  role       = aws_iam_role.health_check_lambda_role.name
  policy_arn = aws_iam_policy.dynamodb_write_policy.arn
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
        Resource = var.dynamodb_table_name_arn
      },
    ]
  })
}