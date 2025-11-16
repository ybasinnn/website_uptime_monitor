resource "aws_apigatewayv2_api" "dashboard_api" {
  name          = "HealthCheckDashboardAPI"
  protocol_type = "HTTP"
  cors_configuration {
    allow_methods = ["GET"]
    allow_origins = ["*"] 
    allow_headers = ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token", "x-amz-user-agent"]
  }
}


resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id             = aws_apigatewayv2_api.dashboard_api.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.dashboard_lambda.invoke_arn
  payload_format_version = "2.0"
}


resource "aws_apigatewayv2_route" "results_route" {
  api_id    = aws_apigatewayv2_api.dashboard_api.id
  route_key = "GET /results"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}


resource "aws_apigatewayv2_stage" "api_stage" {
  api_id = aws_apigatewayv2_api.dashboard_api.id
  name   = "$default" 
  auto_deploy = true
}


resource "aws_lambda_permission" "apigw_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dashboard_lambda.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.dashboard_api.execution_arn}/*/*"
}

