data "local_file" "db_fetcher_lambda_deployment_package" {
  # Point to the exact path of your ZIP file.
  filename = "${path.module}/lambda/db_fetch_results.zip" 
}


resource "aws_lambda_function" "dashboard_lambda" {
  function_name    = "DashboardDataFetcher"
  role             = aws_iam_role.dashboard_lambda_role.arn
  handler          = "db_fetch.lambda_handler"
  runtime          = "python3.11"
  timeout          = 10
  filename         = data.local_file.db_fetcher_lambda_deployment_package.filename
  source_code_hash = data.local_file.db_fetcher_lambda_deployment_package.content_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
    }
  }
}

