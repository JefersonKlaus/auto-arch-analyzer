variable "project_name" {
  description = "Project name used as a prefix for resource names"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket used by Lambda"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table used by Lambda"
  type        = string
}
