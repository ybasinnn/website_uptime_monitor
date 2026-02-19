output "lambda_check_role" {
    description = "The IAM Role ARN for the Lambda function performing health checks."
    value       = aws_iam_role.health_check_lambda_role.name
  
}
output "health_check_lambda_name" {
  description = "The name of the Lambda function performing health checks."
  value       = aws_lambda_function.health_check_lambda.function_name
}

output "checker_function_arn" {
  description = "The ARN of the Lambda function performing health checks."
  value       = aws_lambda_function.health_check_lambda.arn
  
}