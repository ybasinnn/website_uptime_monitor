# Zip just the .py file directly
data "archive_file" "db_fetcher_lambda_deployment_package" {
  type        = "zip"
  source_file = "${path.module}/lambda/db_fetch.py"
  output_path = "${path.module}/lambda/db_fetch_results.zip"
  # Fixed mode so the zip hash is identical locally and in CI (umask differs)
  output_file_mode = "0644"
}

resource "aws_lambda_function" "dashboard_lambda" {
  function_name    = "DashboardDataFetcher"
  role             = aws_iam_role.dashboard_lambda_role.arn
  handler          = "db_fetch.lambda_handler"
  runtime          = "python3.11"
  timeout          = 10
  filename         = data.archive_file.db_fetcher_lambda_deployment_package.output_path
  source_code_hash = data.archive_file.db_fetcher_lambda_deployment_package.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
    }
  }
}