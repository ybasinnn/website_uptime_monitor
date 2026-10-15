variable "lambda_dashboard_arn" {
  type = string
}

variable "lambda_dashbaord_name" {
    type = string
}

variable "allowed_origin" {
  description = "Browser origin allowed to call the API (the dashboard URL)."
  type        = string
}

variable "throttling_burst_limit" {
  description = "Maximum concurrent request burst for the public API."
  type        = number
  default     = 10
}

variable "throttling_rate_limit" {
  description = "Steady-state requests per second allowed on the public API."
  type        = number
  default     = 5
}
