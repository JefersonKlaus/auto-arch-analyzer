variable "rest_api_id" {
  description = "The ID of the API Gateway REST API"
  type        = string
}

variable "parent_id" {
  description = "The parent resource ID for the API Gateway resource"
  type        = string
}

variable "path_part" {
  description = "The path part for the API Gateway resource"
  type        = string
}

variable "path_full" {
  description = "Full path for constructing the full source ARN"
  type        = string
  default     = ""
}

variable "http_methods" {
  description = "The HTTP methods for the API Gateway methods"
  type        = list(string)
}

variable "lambda_function_names" {
  description = "A map of HTTP methods to Lambda function names"
  type        = map(string)
}

variable "region" {
  description = "The AWS region"
  type        = string
}

variable "account_id" {
  description = "The AWS account ID"
  type        = string
}

variable "enable_cors" {
  description = "Enable CORS for the API Gateway resource"
  type        = bool
  default     = true
}

variable "integration_timeout_milliseconds" {
  description = "Integration timeout in milliseconds (max 29000 for API Gateway)"
  type        = number
  default     = 29000
}
