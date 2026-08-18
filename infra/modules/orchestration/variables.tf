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

variable "file_validator_lambda_arn" {
  description = "ARN of the File Validator Lambda invoked by Step Functions"
  type        = string
}

variable "ai_processor_lambda_arn" {
  description = "ARN of the AI Processor Lambda invoked by Step Functions"
  type        = string
}

variable "ia_consumer_lambda_arn" {
  description = "ARN of the IA Consumer Lambda invoked by Step Functions"
  type        = string
}

variable "report_adapter_lambda_arn" {
  description = "ARN of the Report Adapter Lambda invoked by Step Functions"
  type        = string
}

variable "error_logger_lambda_arn" {
  description = "ARN of the Error Logger Lambda invoked by Step Functions on failure"
  type        = string
}
