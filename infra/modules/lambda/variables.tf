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
  default     = "auto-arch-analyzer-diagram-upload-dev"
}

variable "sqs_ingestion_queue_url" {
  description = "SQS ingestion queue URL"
  type        = string
}

variable "sqs_ingestion_queue_arn" {
  description = "SQS ingestion queue ARN"
  type        = string
}


variable "stepfunction_state_machine_arn" {
  description = "Step Functions state machine ARN"
  type        = string
}

variable "common_layer_arn" {
  description = "ARN of the shared common Lambda layer"
  type        = string
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for persisting analysis results"
  type        = string
}

variable "reports_pdf_bucket_name" {
  description = "S3 bucket name used to store generated PDF reports"
  type        = string
}

variable "ses_from_email" {
  description = "Verified SES e-mail identity used as the sender"
  type        = string
}

variable "sqs_pdf_mail_queue_url" {
  description = "SQS URL for the PDF/Mail queue"
  type        = string
}

variable "sqs_pdf_mail_queue_arn" {
  description = "SQS ARN for the PDF/Mail queue"
  type        = string
}
