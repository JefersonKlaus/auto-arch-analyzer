variable "project_name" {
  description = "Project name used as a prefix for resource names"
  type        = string
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "s3_bucket_arns" {
  description = "ARNs of S3 buckets used by Lambda"
  type        = list(string)
}

variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table used by Lambda"
  type        = string
}

variable "bedrock_model_id" {
  description = "The ID of the Bedrock model that the Lambda function is allowed to invoke."
  type        = string
}

variable "lambda_arns_for_sfn" {
  description = "A list of Lambda function ARNs that the Step Functions state machine can invoke."
  type        = list(string)
  default     = []
}
variable "stepfunction_state_machine_arn" {
  description = "ARN of the Step Functions state machine started by the init Lambda"
  type        = string
}
