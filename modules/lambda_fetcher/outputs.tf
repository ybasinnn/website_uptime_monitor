output "dashboard_role" {
  value = aws_iam_role.dashboard_lambda_role.name
}

output "dashboard_lambda_arn" {
  value = aws_lambda_function.dashboard_lambda.arn
}

output "dashboard_lambda_name" {
  value = aws_lambda_function.dashboard_lambda.function_name
}
