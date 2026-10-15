resource "aws_apigatewayv2_api" "dashboard_api" {
  name          = "HealthCheckDashboardAPI"
  protocol_type = "HTTP"
  cors_configuration {
    allow_methods = ["GET"]
    # Only the dashboard may call the API from a browser
    allow_origins = [var.allowed_origin]
    allow_headers = ["content-type"]
  }
}


resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id             = aws_apigatewayv2_api.dashboard_api.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = var.lambda_dashboard_arn
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

  # The endpoint is public and unauthenticated; cap request rate to limit cost abuse
  default_route_settings {
    throttling_burst_limit = var.throttling_burst_limit
    throttling_rate_limit  = var.throttling_rate_limit
  }
}


resource "aws_lambda_permission" "apigw_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_dashbaord_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.dashboard_api.execution_arn}/*/*"
}

