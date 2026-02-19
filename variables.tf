variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string

}

variable "email_endpoint" {
  description = "The email address to subscribe to the SNS topic for notifications."
  type        = string
}

variable "target_url" {
  description = "The url that would be monitored"
  type       = string
}