variable "project_name" {
  description = "Project name used as a prefix for resource names"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB"
  type        = number
}

variable "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  type        = string
}

variable "s3_bucket_id" {
  description = "S3 bucket ID used by Lambda"
  type        = string
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name used by Lambda"
  type        = string
}
