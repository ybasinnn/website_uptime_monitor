resource "aws_dynamodb_table" "health_check_results" {
  name             = "WebsiteHealthCheckResults"
  billing_mode     = "PAY_PER_REQUEST" 
  hash_key         = "Timestamp"
  range_key        = "URL"

  attribute {
    name = "Timestamp"
    type = "S" 
  }

  attribute {
    name = "URL"
    type = "S"
  }

  tags = {
    Name = "WebsiteHealthCheckResults"
  }
}





