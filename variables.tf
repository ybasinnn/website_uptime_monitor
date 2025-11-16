variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "eu-west-1"
  
}

variable "email_endpoint" {
  description = "The email address to subscribe to the SNS topic for notifications."
  type        = string
}

variable "target_url" {
  default = "https://noto360.com"
}