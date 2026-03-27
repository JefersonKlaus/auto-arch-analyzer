output "ingestion_queue_url" {
  description = "URL of the SQS Ingestion Queue"
  value       = module.queue.ingestion_queue_url
}

output "pdf_mail_queue_url" {
  description = "URL of the SQS PDF/Mail Queue"
  value       = module.queue.pdf_mail_queue_url
}

output "s3_bucket_name" {
  description = "Name of the diagrams S3 bucket"
  value       = module.s3.diagram_upload_bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the diagrams S3 bucket"
  value       = module.s3.diagram_upload_bucket_arn
}

output "diagrams_bucket_name" {
  description = "Name of the diagrams S3 bucket"
  value       = module.s3.diagram_upload_bucket_name
}

output "diagrams_bucket_arn" {
  description = "ARN of the diagrams S3 bucket"
  value       = module.s3.diagram_upload_bucket_arn
}

output "reports_pdf_bucket_name" {
  description = "Name of the reports PDF S3 bucket"
  value       = module.s3.analysis_result_bucket_name
}

output "reports_pdf_bucket_arn" {
  description = "ARN of the reports PDF S3 bucket"
  value       = module.s3.analysis_result_bucket_arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for analysis reports"
  value       = module.dynamodb.table_name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = module.dynamodb.table_arn
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

output "lambda_analyze_function_name" {
  description = "Name of the Analyze Architecture Lambda function"
  value       = module.lambda.analyze_function_name
}

output "lambda_analyze_function_arn" {
  description = "ARN of the Analyze Architecture Lambda function"
  value       = module.lambda.analyze_function_arn
}
