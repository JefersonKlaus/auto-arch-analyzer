variable "project_name" {
  description = "Project name used as prefix for API and queue resources"
  type        = string
}

variable "environment" {
  description = "Deployment environment used as API Gateway stage name"
  type        = string
}

variable "aws_region" {
  description = "AWS region where resources are deployed"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID used to build API Gateway -> SQS integration URI"
  type        = string
}

variable "ingestion_queue_name" {
  description = "Name of the ingestion queue used by API Gateway integration"
  type        = string
}

variable "ingestion_queue_arn" {
  description = "ARN of the ingestion queue used in API Gateway IAM policy"
  type        = string
}

variable "analyze_lambda_function_name" {
  description = "Legacy compatibility input; currently unused by direct API Gateway -> SQS integration"
  type        = string
  default     = null
}
