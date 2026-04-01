variable "lambda_role_arn" {
  description = "The ARN of the IAM role to be assumed by the Lambda function"
  type        = string
}

variable "project_name" {
  description = "Project name used as a prefix for resource names"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, staging, prod)"
  type        = string
}

variable "s3_diagram_bucket" {
  description = "S3 bucket name for diagram uploads"
  type        = string
}

variable "sqs_ingestion_queue_url" {
  description = "SQS ingestion queue URL"
  type        = string
}
