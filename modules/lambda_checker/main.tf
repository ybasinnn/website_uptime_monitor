data "local_file" "website_checker_lambda_deployment_package" {
  # Point to the exact path of your ZIP file.
  filename = "${path.module}/lambda/website_check.zip" 
}



resource "aws_lambda_function" "health_check_lambda" {
  # ... other configuration (e.g., runtime, handler) ...
  
  function_name    = "WebsiteHealthChecker"
  role             = aws_iam_role.health_check_lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  
  filename         = data.local_file.website_checker_lambda_deployment_package.filename
  source_code_hash = data.local_file.website_checker_lambda_deployment_package.content_base64sha256
  
    environment {
    variables = {
      SNS_TOPIC_ARN   = var.sns_topic_arn
      TARGET_URL      = var.target_url
      DYNAMODB_TABLE  = var.dynamodb_table_name
  }
  }
}




