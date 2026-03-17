variable "project_name" {
  description = "Project name used as a prefix for resource names"
  type        = string
}

variable "sfn_role_arn" {
  description = "ARN of the Step Functions execution role"
  type        = string
}

variable "sfn_role_id" {
  description = "ID of the Step Functions execution role"
  type        = string
}

variable "lambda_function_arn" {
  description = "ARN of the Lambda function invoked by Step Functions"
  type        = string
}
