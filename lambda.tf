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

resource "aws_sns_topic" "website_alerts" {
  name = "WebsiteHealthCheckTopic"
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
      Resource = aws_sns_topic.website_alerts.arn
    }]
  })
}

# Attach policies to the role
resource "aws_iam_role_policy_attachment" "lambda_log_attach" {
  role       = aws_iam_role.health_check_lambda_role.name
  policy_arn = aws_iam_policy.lambda_logging_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_sns_attach" {
  role       = aws_iam_role.health_check_lambda_role.name
  policy_arn = aws_iam_policy.sns_publish_policy.arn
}


data "local_file" "lambda_deployment_package" {
  # Point to the exact path of your ZIP file.
  filename = "lambda/deployment_package.zip" 
}


resource "aws_lambda_function" "health_check_lambda" {
  # ... other configuration (e.g., runtime, handler) ...
  
  function_name    = "WebsiteHealthChecker"
  role             = aws_iam_role.health_check_lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  
  filename         = data.local_file.lambda_deployment_package.filename
  source_code_hash = data.local_file.lambda_deployment_package.content_base64sha256
  
  # Crucial: Pass the DynamoDB table name and URL to the function
  environment {
    variables = {
      SNS_TOPIC_ARN   = aws_sns_topic.website_alerts.arn
      TARGET_URL      = var.target_url
      DYNAMODB_TABLE  = aws_dynamodb_table.health_check_results.name # <-- New Environment Variable
    }
  }
}





