output "table_arn" {
  value = aws_dynamodb_table.health_check_results.arn
}

output "table_name" {
  value = aws_dynamodb_table.health_check_results.name
}
