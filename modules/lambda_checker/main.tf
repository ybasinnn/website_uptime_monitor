# Zip just the .py file directly (stdlib only, no third-party dependencies)
data "archive_file" "website_checker_lambda_deployment_package" {
  type        = "zip"
  source_file = "${path.module}/lambda/lambda_function.py"
  output_path = "${path.module}/lambda/website_check.zip"
}



resource "aws_lambda_function" "health_check_lambda" {
  function_name = "WebsiteHealthChecker"
  role          = aws_iam_role.health_check_lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30

  filename         = data.archive_file.website_checker_lambda_deployment_package.output_path
  source_code_hash = data.archive_file.website_checker_lambda_deployment_package.output_base64sha256

  environment {
    variables = {
      SNS_TOPIC_ARN  = var.sns_topic_arn
      TARGET_URL     = var.target_url
      DYNAMODB_TABLE = var.dynamodb_table_name
    }
  }
}




