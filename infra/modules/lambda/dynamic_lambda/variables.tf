variable "lambda_role_arn" {
  description = "The ARN of the IAM role to be assumed by the Lambda function"
  type        = string
}

variable "source_dir" {
  description = "The source directory of the Lambda function"
  type        = string
}

variable "handler" {
  description = "The handler of the Lambda function"
  type        = string
}

variable "runtime" {
  description = "The runtime of the Lambda function"
  type        = string
}

variable "lambda_function_name" {
  description = "The name of the Lambda function"
  type        = string
}

variable "environment_variables" {
  description = "Dictionary of environment variables for the Lambda function"
  type        = map(string)
}

variable "timeout" {
  description = "The amount of time the Lambda function has to run in seconds"
  type        = number
  default     = 10
}
