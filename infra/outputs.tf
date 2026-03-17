# output "api_gateway_invoke_url" {
#   description = "Base invoke URL of the API Gateway stage"
#   value       = module.network.api_gateway_invoke_url
# }

output "s3_bucket_name" {
  description = "Name of the S3 bucket used to store architecture diagrams"
  value       = module.storage.s3_bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.storage.s3_bucket_arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for analysis reports"
  value       = module.storage.dynamodb_table_name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = module.storage.dynamodb_table_arn
}

# output "step_functions_arn" {
#   description = "ARN of the Step Functions state machine"
#   value       = module.orchestration.step_functions_arn
# }

# output "lambda_function_name" {
#   description = "Name of the AI processor Lambda function"
#   value       = module.compute.lambda_function_name
# }

# output "lambda_function_arn" {
#   description = "ARN of the AI processor Lambda function"
#   value       = module.compute.lambda_function_arn
# }
