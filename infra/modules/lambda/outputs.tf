output "file_validator_function_arn" {
  description = "ARN of the File Validator Lambda function"
  value       = module.file_validator.lambda_function_arn
}

output "ai_processor_function_arn" {
  description = "ARN of the AI Processor Lambda function"
  value       = module.ai_processor.lambda_function_arn
}

output "report_adapter_function_arn" {
  description = "ARN of the Report Adapter Lambda function"
  value       = module.report_adapter.lambda_function_arn
}

output "error_logger_function_arn" {
  description = "ARN of the Error Logger Lambda function"
  value       = module.error_logger.lambda_function_arn
}

output "init_lambda_function_arn" {
  description = "ARN of the Init lambda function"
  value       = module.init_lambda.lambda_function_arn
}
